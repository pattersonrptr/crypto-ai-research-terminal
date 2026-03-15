"""Scheduler jobs — periodic data collection and scoring pipeline.

Phase 8: full pipeline with job health monitoring and Redis dead-letter queue.
Phase 10: narrative snapshot persistence and category-based narrative building.
Phase 11: alert generation via AlertEvaluator after scoring.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

import structlog

from app.alerts.alert_evaluator import AlertEvaluator
from app.analysis.narrative_persister import NarrativePersister
from app.collectors.coingecko_collector import CoinGeckoCollector
from app.config import Settings
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from app.processors.market_processor import MarketProcessor
from app.scoring.fundamental_scorer import FundamentalScorer
from app.scoring.heuristic_sub_scorer import HeuristicSubScorer
from app.scoring.opportunity_engine import OpportunityEngine

if TYPE_CHECKING:
    import redis.asyncio as aioredis
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.alert import Alert
    from app.models.narrative import NarrativeCluster

logger = structlog.get_logger(__name__)

# Redis key templates
_JOB_HASH_KEY = "scheduler:job:{job_name}"
_JOB_DLQ_KEY = "scheduler:dlq:{job_name}"

# Max tokens to fetch categories for (rate-limit friendly)
_NARRATIVE_CATEGORY_LIMIT = 20


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

    settings = Settings()
    api_key = settings.coingecko_api_key

    try:
        async with CoinGeckoCollector(api_key=api_key) as collector:
            raw_data = await collector.collect(symbols=[])

        results: list[dict[str, Any]] = []
        for raw in raw_data:
            try:
                processed = MarketProcessor.process(raw)
                fundamental_score = FundamentalScorer.score(processed)
                sub_scores = HeuristicSubScorer.score(processed)
                opportunity_score = OpportunityEngine.full_composite_score(
                    fundamental=fundamental_score,
                    growth=sub_scores.growth_score,
                    narrative=sub_scores.narrative_score,
                    listing=sub_scores.listing_probability,
                    risk=sub_scores.risk_score,
                    cycle_leader_prob=sub_scores.cycle_leader_prob,
                )
                results.append(
                    {
                        **processed,
                        "fundamental_score": fundamental_score,
                        "opportunity_score": opportunity_score,
                        **sub_scores.to_dict(),
                    }
                )
            except Exception:
                log.exception("daily_collection_job.token_error", symbol=raw.get("symbol"))

        log.info("daily_collection_job.scored", count=len(results))
        await _persist_results(results)

        # Build and persist narrative snapshots from token categories
        try:
            # Fetch categories for top tokens via /coins/{id} detail endpoint
            top_ids = [r.get("coingecko_id", "") for r in raw_data if r.get("coingecko_id")]
            top_ids = top_ids[:_NARRATIVE_CATEGORY_LIMIT]

            categories_map: dict[str, list[str]] = {}
            if top_ids:
                async with CoinGeckoCollector(api_key=api_key) as cat_collector:
                    categories_map = await cat_collector.collect_categories(top_ids)

            narrative_data = [
                {
                    "symbol": r.get("symbol", "").upper(),
                    "name": r.get("name", ""),
                    "categories": categories_map.get(r.get("coingecko_id", ""), []),
                }
                for r in raw_data
                if r.get("coingecko_id", "") in categories_map
            ]
            clusters = build_narrative_snapshot_from_categories(narrative_data)
            await persist_narrative_snapshot(clusters)
            log.info(
                "daily_collection_job.narratives_persisted",
                count=len(clusters),
            )
        except Exception:
            log.exception("daily_collection_job.narrative_snapshot_error")

        # Evaluate alert rules against scored results and persist triggered alerts
        try:
            triggered = await evaluate_and_persist_alerts(results)
            log.info(
                "daily_collection_job.alerts_evaluated",
                count=len(triggered),
            )
        except Exception:
            log.exception("daily_collection_job.alert_evaluation_error")

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
                technology_score=float(item.get("technology_score", 0.0)),
                tokenomics_score=float(item.get("tokenomics_score", 0.0)),
                adoption_score=float(item.get("adoption_score", 0.0)),
                dev_activity_score=float(item.get("dev_activity_score", 0.0)),
                narrative_score=float(item.get("narrative_score", 0.0)),
                growth_score=float(item.get("growth_score", 0.0)),
                risk_score=float(item.get("risk_score", 0.0)),
                listing_probability=float(item.get("listing_probability", 0.0)),
                cycle_leader_prob=float(item.get("cycle_leader_prob", 0.0)),
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


# ---------------------------------------------------------------------------
# Phase 10: Narrative snapshot helpers
# ---------------------------------------------------------------------------


async def persist_narrative_snapshot(
    clusters: list[NarrativeCluster],
    *,
    session: AsyncSession | None = None,
) -> None:
    """Persist a list of :class:`NarrativeCluster` rows to the database.

    Args:
        clusters: Narrative cluster ORM objects to persist.
        session: Optional externally-managed session (used by tests).
    """
    if not clusters:
        logger.info("persist_narrative_snapshot.empty")
        return

    own_session = False
    if session is None:
        from app.db.session import _SessionLocal  # noqa: PLC0415

        session = _SessionLocal()
        own_session = True

    try:
        for cluster in clusters:
            session.add(cluster)
        await session.commit()
        logger.info("persist_narrative_snapshot.committed", count=len(clusters))
    except Exception:
        await session.rollback()
        logger.exception("persist_narrative_snapshot.failed")
        raise
    finally:
        if own_session:
            await session.close()


def build_narrative_snapshot_from_categories(
    token_data: list[dict[str, Any]],
    *,
    snapshot_date: date | None = None,
) -> list[NarrativeCluster]:
    """Build narrative clusters from CoinGecko category metadata.

    Groups tokens by their categories and creates one
    :class:`NarrativeCluster` per category that contains ≥ 2 tokens.

    Args:
        token_data: List of dicts with at least ``symbol`` and ``categories``.
        snapshot_date: Date for the snapshot. Defaults to today.

    Returns:
        List of :class:`NarrativeCluster` objects (not yet persisted).
    """
    snap = snapshot_date or date.today()
    return NarrativePersister.build_from_categories(token_data, snapshot_date=snap)


# ---------------------------------------------------------------------------
# Phase 11: Alert evaluation helpers
# ---------------------------------------------------------------------------


async def evaluate_and_persist_alerts(
    results: list[dict[str, Any]],
    *,
    session: AsyncSession | None = None,
) -> list[Alert]:
    """Run AlertEvaluator on scored results and persist triggered alerts.

    Args:
        results: Scored pipeline output dicts.
        session: Optional externally-managed session (used by tests).

    Returns:
        List of persisted Alert ORM objects.
    """
    evaluator = AlertEvaluator()
    alerts = evaluator.evaluate_batch(results)

    if not alerts:
        logger.info("evaluate_and_persist_alerts.none_triggered")
        return []

    own_session = False
    if session is None:
        from app.db.session import _SessionLocal  # noqa: PLC0415

        session = _SessionLocal()
        own_session = True

    try:
        for alert in alerts:
            session.add(alert)
        await session.commit()
        logger.info("evaluate_and_persist_alerts.committed", count=len(alerts))
    except Exception:
        await session.rollback()
        logger.exception("evaluate_and_persist_alerts.failed")
        raise
    finally:
        if own_session:
            await session.close()

    return alerts
