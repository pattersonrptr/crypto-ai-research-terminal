"""Scheduler jobs — periodic data collection and scoring pipeline."""

from __future__ import annotations

import structlog

from app.collectors.coingecko_collector import CoinGeckoCollector
from app.processors.market_processor import MarketProcessor
from app.scoring.fundamental_scorer import FundamentalScorer
from app.scoring.opportunity_engine import OpportunityEngine

logger = structlog.get_logger(__name__)


async def daily_collection_job() -> None:
    """Collect market data, process, score, and persist results for all tracked tokens."""
    log = logger.bind(job="daily_collection_job")
    log.info("daily_collection_job.started")

    collector = CoinGeckoCollector()
    raw_data = await collector.collect(symbols=[])  # empty → fetch top-N tokens

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


async def _persist_results(results: list[dict[str, object]]) -> None:
    """Persist scored results to the database (Phase 1: stub — DB not yet wired)."""
    logger.info("_persist_results.called", count=len(results))
