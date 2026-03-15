"""TDD tests for Phase 9 pipeline — full scoring through _persist_results.

Validates that daily_collection_job pipeline computes all 11 sub-scores
and _persist_results writes them to the database.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.score import TokenScore
from tests.conftest_helpers import create_sqlite_tables


@pytest.fixture
async def async_engine():  # type: ignore[return]
    """Create an in-memory async SQLite engine with the full schema."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(create_sqlite_tables)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):  # type: ignore[return]
    """Provide an AsyncSession bound to the in-memory engine."""
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


_FULL_RESULT: dict[str, Any] = {
    "coingecko_id": "ethereum",
    "symbol": "ETH",
    "name": "Ethereum",
    "price_usd": 3500.0,
    "market_cap_usd": 420_000_000_000.0,
    "volume_24h_usd": 15_000_000_000.0,
    "rank": 2,
    "ath_usd": 4800.0,
    "circulating_supply": 120_000_000.0,
    "volume_mcap_ratio": 0.036,
    "price_velocity": 2.5,
    "ath_distance_pct": 27.1,
    # Core scores
    "fundamental_score": 0.82,
    "opportunity_score": 0.75,
    # Sub-scores (all 9)
    "technology_score": 0.65,
    "tokenomics_score": 0.70,
    "adoption_score": 0.80,
    "dev_activity_score": 0.55,
    "narrative_score": 0.60,
    "growth_score": 0.50,
    "risk_score": 0.85,
    "listing_probability": 0.90,
    "cycle_leader_prob": 0.40,
}


class TestPersistResultsAllSubScores:
    """_persist_results must write all 11 sub-scores to token_scores table."""

    @pytest.mark.asyncio
    async def test_persist_results_writes_all_sub_scores(self, async_session: AsyncSession) -> None:
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_FULL_RESULT], session=async_session)

        score = (await async_session.execute(select(TokenScore))).scalars().first()
        assert score is not None

        # Core
        assert score.fundamental_score == pytest.approx(0.82)
        assert score.opportunity_score == pytest.approx(0.75)

        # Sub-scores
        assert score.technology_score == pytest.approx(0.65)
        assert score.tokenomics_score == pytest.approx(0.70)
        assert score.adoption_score == pytest.approx(0.80)
        assert score.dev_activity_score == pytest.approx(0.55)
        assert score.narrative_score == pytest.approx(0.60)
        assert score.growth_score == pytest.approx(0.50)
        assert score.risk_score == pytest.approx(0.85)
        assert score.listing_probability == pytest.approx(0.90)
        assert score.cycle_leader_prob == pytest.approx(0.40)

    @pytest.mark.asyncio
    async def test_persist_results_defaults_missing_sub_scores_to_zero(
        self, async_session: AsyncSession
    ) -> None:
        """When pipeline data lacks sub-scores, they should default to 0.0."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        minimal: dict[str, Any] = {
            "coingecko_id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": 60000.0,
            "market_cap_usd": 1_200_000_000_000.0,
            "volume_24h_usd": 30_000_000_000.0,
            "rank": 1,
            "ath_usd": 73000.0,
            "circulating_supply": 19_000_000.0,
            "fundamental_score": 0.75,
            "opportunity_score": 0.75,
        }
        await _persist_results([minimal], session=async_session)

        score = (await async_session.execute(select(TokenScore))).scalars().first()
        assert score is not None
        assert score.technology_score == pytest.approx(0.0)
        assert score.growth_score == pytest.approx(0.0)
        assert score.risk_score == pytest.approx(0.0)
