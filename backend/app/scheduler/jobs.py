"""Scheduler jobs — periodic data collection and scoring pipeline.

Phase 8: full pipeline with job health monitoring and Redis dead-letter queue.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from app.collectors.coingecko_collector import CoinGeckoCollector
from app.processors.market_processor import MarketProcessor
from app.scoring.fundamental_scorer import FundamentalScorer
from app.scoring.opportunity_engine import OpportunityEngine

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = structlog.get_logger(__name__)

# Redis key templates
_JOB_HASH_KEY = "scheduler:job:{job_name}"
_JOB_DLQ_KEY = "scheduler:dlq:{job_name}"


# ---------------------------------------------------------------------------
# Health monitoring helpers
# ---------------------------------------------------------------------------


async def record_job_success(
    redis: aioredis.Redis[bytes],
    job_name: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record a successful job execution in Redis.

    Args:
        redis: Async Redis client.
        job_name: Scheduler job identifier.
        metadata: Optional extra data to store (e.g. count of processed tokens).
    """
    now = datetime.now(tz=UTC).isoformat()
    payload: dict[str | bytes, str | bytes] = {
        "last_run": now,
        "last_status": "success",
        "error_count": "0",
        "last_error": "",
    }
    if metadata:
        payload["metadata"] = json.dumps(metadata)
    await redis.hset(_JOB_HASH_KEY.format(job_name=job_name), mapping=payload)
    logger.info("scheduler.job.success", job=job_name, ts=now)


async def record_job_failure(
    redis: aioredis.Redis[bytes],
    job_name: str,
    error: str,
) -> None:
    """Record a failed job execution in Redis and push to the dead-letter queue.

    Args:
        redis: Async Redis client.
        job_name: Scheduler job identifier.
        error: Error message/description.
    """
    now = datetime.now(tz=UTC).isoformat()
    key = _JOB_HASH_KEY.format(job_name=job_name)

    # Increment error count atomically
    await redis.hincrby(key, "error_count", 1)
    await redis.hset(
        key,
        mapping={
            b"last_run": now.encode(),
            b"last_status": b"failure",
            b"last_error": error.encode(),
        },
    )
    # Push to dead-letter queue for inspection
    dlq_entry = json.dumps({"job": job_name, "error": error, "ts": now})
    await redis.rpush(_JOB_DLQ_KEY.format(job_name=job_name), dlq_entry)
    logger.error("scheduler.job.failure", job=job_name, error=error, ts=now)


async def get_job_status(
    redis: aioredis.Redis[bytes],
    job_name: str,
) -> dict[str, Any]:
    """Retrieve job health status from Redis.

    Args:
        redis: Async Redis client.
        job_name: Scheduler job identifier.

    Returns:
        Dict with keys: ``job_name``, ``last_run``, ``last_status``,
        ``error_count``, ``last_error``.  Fields are ``None`` when the
        job has never run.
    """
    raw: dict[bytes, bytes] = await redis.hgetall(_JOB_HASH_KEY.format(job_name=job_name))
    if not raw:
        return {
            "job_name": job_name,
            "last_run": None,
            "last_status": None,
            "error_count": 0,
            "last_error": None,
        }

    def _decode(field: str) -> str | None:
        val: bytes | None = raw.get(field.encode())
        if val is None:
            return None
        return val.decode()

    return {
        "job_name": job_name,
        "last_run": _decode("last_run"),
        "last_status": _decode("last_status"),
        "error_count": int(_decode("error_count") or 0),
        "last_error": _decode("last_error") or None,
    }


# ---------------------------------------------------------------------------
# Job definitions
# ---------------------------------------------------------------------------

_JOB_NAME = "daily_collection_job"


async def daily_collection_job(
    redis: aioredis.Redis[bytes] | None = None,
) -> None:
    """Collect market data, process, score, persist, and record health status.

    Full pipeline:
      CoinGeckoCollector.collect → MarketProcessor.process →
      FundamentalScorer.score → OpportunityEngine.composite_score →
      _persist_results → record_job_success / record_job_failure

    Args:
        redis: Optional async Redis client for health monitoring. When
               ``None`` the health recording steps are skipped (useful
               for manual/test runs without Redis).
    """
    log = logger.bind(job=_JOB_NAME)
    log.info("daily_collection_job.started")

    try:
        collector = CoinGeckoCollector()
        raw_data = await collector.collect(symbols=[])

        results: list[dict[str, object]] = []
        for raw in raw_data:
            try:
                processed = MarketProcessor.process(raw)
                fundamental_score = FundamentalScorer.score(processed)
                opportunity_score = OpportunityEngine.composite_score(fundamental_score)
                results.append(
                    {
                        **processed,
                        "fundamental_score": fundamental_score,
                        "opportunity_score": opportunity_score,
                    }
                )
            except Exception:
                log.exception("daily_collection_job.token_error", symbol=raw.get("symbol"))

        log.info("daily_collection_job.scored", count=len(results))
        await _persist_results(results)
        log.info("daily_collection_job.completed", count=len(results))

        if redis is not None:
            await record_job_success(
                redis=redis,
                job_name=_JOB_NAME,
                metadata={"token_count": len(results)},
            )

    except Exception as exc:
        log.exception("daily_collection_job.fatal_error")
        if redis is not None:
            await record_job_failure(
                redis=redis,
                job_name=_JOB_NAME,
                error=str(exc),
            )


async def _persist_results(results: list[dict[str, object]]) -> None:
    """Persist scored results to the database (stub — full DB wiring in production)."""
    logger.info("_persist_results.called", count=len(results))
