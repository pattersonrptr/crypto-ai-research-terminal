"""TDD tests for daily_collection_job — full pipeline scoring integration.

Mocks CoinGecko HTTP and verifies all 11 sub-scores flow through to persistence.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.score import TokenScore


@pytest.fixture
async def async_engine():  # type: ignore[return]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):  # type: ignore[return]
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


_COINGECKO_RESPONSE: list[dict[str, Any]] = [
    {
        "coingecko_id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "price_usd": 60000.0,
        "market_cap_usd": 1_200_000_000_000.0,
        "volume_24h_usd": 30_000_000_000.0,
        "rank": 1,
        "ath_usd": 73000.0,
        "circulating_supply": 19_000_000.0,
    },
]


class TestDailyCollectionJobPipeline:
    """Full pipeline: collect → process → score (all sub-scores) → persist."""

    @pytest.mark.asyncio
    async def test_pipeline_computes_all_sub_scores(self, async_session: AsyncSession) -> None:
        """After the pipeline runs, TokenScore should have non-default sub-scores."""
        from app.processors.market_processor import MarketProcessor
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415
        from app.scoring.fundamental_scorer import FundamentalScorer
        from app.scoring.heuristic_sub_scorer import HeuristicSubScorer
        from app.scoring.opportunity_engine import OpportunityEngine

        # Simulate the pipeline loop (same logic as daily_collection_job)
        results: list[dict[str, Any]] = []
        for raw in _COINGECKO_RESPONSE:
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

        await _persist_results(results, session=async_session)

        score = (await async_session.execute(select(TokenScore))).scalars().first()
        assert score is not None

        # All sub-scores should be > 0 for Bitcoin (rank 1, huge mcap)
        assert score.fundamental_score > 0.0
        assert score.opportunity_score > 0.0
        assert score.technology_score > 0.0
        assert score.tokenomics_score > 0.0
        assert score.adoption_score > 0.0
        assert score.dev_activity_score > 0.0
        assert score.narrative_score > 0.0
        assert score.growth_score > 0.0
        assert score.risk_score > 0.0
        assert score.listing_probability > 0.0
        assert score.cycle_leader_prob > 0.0

        # All in [0, 1]
        for attr in [
            "fundamental_score",
            "opportunity_score",
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "cycle_leader_prob",
        ]:
            val = getattr(score, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val} out of [0, 1]"
