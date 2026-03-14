"""TDD tests for TokenScore model — all 11 sub-score columns must exist.

Phase 9: The model must store technology, tokenomics, adoption, dev_activity,
narrative, growth, risk, listing_probability, and cycle_leader_prob alongside
the existing fundamental and opportunity scores.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.score import TokenScore
from app.models.token import Token


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


class TestTokenScoreSubScoreColumns:
    """TokenScore model must have all 11 sub-score columns per SCOPE.md §7."""

    @pytest.mark.asyncio
    async def test_token_score_has_all_sub_score_columns(self, async_session: AsyncSession) -> None:
        """All 11 score columns must be writable and readable."""
        token = Token(symbol="TEST", name="Test Token", coingecko_id="test-token")
        async_session.add(token)
        await async_session.flush()

        score = TokenScore(
            token_id=token.id,
            fundamental_score=0.75,
            technology_score=0.60,
            tokenomics_score=0.55,
            adoption_score=0.70,
            dev_activity_score=0.65,
            narrative_score=0.80,
            growth_score=0.72,
            risk_score=0.45,
            listing_probability=0.30,
            cycle_leader_prob=0.15,
            opportunity_score=0.68,
        )
        async_session.add(score)
        await async_session.commit()

        row = (await async_session.execute(select(TokenScore))).scalars().first()
        assert row is not None
        assert row.fundamental_score == pytest.approx(0.75)
        assert row.technology_score == pytest.approx(0.60)
        assert row.tokenomics_score == pytest.approx(0.55)
        assert row.adoption_score == pytest.approx(0.70)
        assert row.dev_activity_score == pytest.approx(0.65)
        assert row.narrative_score == pytest.approx(0.80)
        assert row.growth_score == pytest.approx(0.72)
        assert row.risk_score == pytest.approx(0.45)
        assert row.listing_probability == pytest.approx(0.30)
        assert row.cycle_leader_prob == pytest.approx(0.15)
        assert row.opportunity_score == pytest.approx(0.68)

    @pytest.mark.asyncio
    async def test_token_score_sub_scores_default_to_zero(
        self, async_session: AsyncSession
    ) -> None:
        """Sub-scores should default to 0.0 when not provided."""
        token = Token(symbol="DEF", name="Default Token", coingecko_id="default-token")
        async_session.add(token)
        await async_session.flush()

        score = TokenScore(
            token_id=token.id,
            fundamental_score=0.50,
            opportunity_score=0.50,
        )
        async_session.add(score)
        await async_session.commit()

        row = (await async_session.execute(select(TokenScore))).scalars().first()
        assert row is not None
        assert row.technology_score == pytest.approx(0.0)
        assert row.tokenomics_score == pytest.approx(0.0)
        assert row.adoption_score == pytest.approx(0.0)
        assert row.dev_activity_score == pytest.approx(0.0)
        assert row.narrative_score == pytest.approx(0.0)
        assert row.growth_score == pytest.approx(0.0)
        assert row.risk_score == pytest.approx(0.0)
        assert row.listing_probability == pytest.approx(0.0)
        assert row.cycle_leader_prob == pytest.approx(0.0)
