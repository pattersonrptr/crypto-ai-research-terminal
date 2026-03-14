"""Scheduler jobs — periodic data collection and scoring pipeline.

Phase 8: full pipeline with job health monitoring and Redis dead-letter queue.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from app.collectors.coingecko_collector import CoinGeckoCollector
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from app.processors.market_processor import MarketProcessor
from app.scoring.fundamental_scorer import FundamentalScorer
from app.scoring.opportunity_engine import OpportunityEngine

if TYPE_CHECKING:
    import redis.asyncio as aioredis
    from sqlalchemy.ext.asyncio import AsyncSession

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
        async with CoinGeckoCollector() as collector:
            raw_data = await collector.collect(symbols=[])

        results: list[dict[str, Any]] = []
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


async def _persist_results(
    results: list[dict[str, Any]],
    *,
    session: AsyncSession | None = None,
) -> None:
    """Persist scored results to tokens, token_scores and market_data tables.

    Args:
        results: Pipeline output dicts containing token info + scores.
        session: Optional externally-managed session (used by tests).
                 When ``None`` the function creates its own session.
    """
    if not results:
        logger.info("_persist_results.empty")
        return

    from sqlalchemy import select  # noqa: PLC0415

    own_session = False
    if session is None:
        from app.db.session import _SessionLocal  # noqa: PLC0415

        session = _SessionLocal()
        own_session = True

    try:
        for item in results:
            symbol = str(item["symbol"])
            coingecko_id = str(item["coingecko_id"])
            name = str(item["name"])

            # Upsert token (get-or-create by coingecko_id, fallback by symbol)
            stmt = select(Token).where(Token.coingecko_id == coingecko_id)
            token: Token | None = (await session.execute(stmt)).scalars().first()
            if token is None:
                # Also check by symbol — CoinGecko can return duplicate symbols
                sym_stmt = select(Token).where(Token.symbol == symbol.upper())
                token = (await session.execute(sym_stmt)).scalars().first()
            if token is None:
                token = Token(
                    symbol=symbol.upper(),
                    name=name,
                    coingecko_id=coingecko_id,
                )
                session.add(token)
                await session.flush()  # generate token.id
            else:
                # Skip score/market_data for the duplicate-symbol variant
                if token.coingecko_id != coingecko_id:
                    logger.debug(
                        "_persist_results.skip_duplicate_symbol",
                        symbol=symbol,
                        existing_id=token.coingecko_id,
                        incoming_id=coingecko_id,
                    )
                    continue

            # Insert score snapshot
            score = TokenScore(
                token_id=token.id,
                fundamental_score=float(item.get("fundamental_score", 0.0)),
                opportunity_score=float(item.get("opportunity_score", 0.0)),
            )
            session.add(score)

            # Insert market data snapshot
            md = MarketData(
                token_id=token.id,
                price_usd=float(item.get("price_usd", 0.0)),
                market_cap_usd=float(item.get("market_cap_usd", 0.0)),
                volume_24h_usd=float(item.get("volume_24h_usd", 0.0)),
                rank=int(item["rank"]) if item.get("rank") is not None else None,
                ath_usd=float(item["ath_usd"]) if item.get("ath_usd") is not None else None,
                circulating_supply=(
                    float(item["circulating_supply"])
                    if item.get("circulating_supply") is not None
                    else None
                ),
            )
            session.add(md)

        await session.commit()
        logger.info("_persist_results.committed", count=len(results))
    except Exception:
        await session.rollback()
        logger.exception("_persist_results.failed")
        raise
    finally:
        if own_session:
            await session.close()
