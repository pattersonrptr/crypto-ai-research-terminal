"""Tests for category persistence in the pipeline (Phase 15).

Verifies that _persist_results writes token_category to Token.category,
and that existing tokens with null category get backfilled on subsequent runs.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.token import Token
from tests.conftest_helpers import create_sqlite_tables

# ---------------------------------------------------------------------------
# Fixtures — in-memory async SQLite engine
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_engine():  # type: ignore[return]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(create_sqlite_tables)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):  # type: ignore[return]
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_RESULT_BTC: dict[str, object] = {
    "coingecko_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "price_usd": 60000.0,
    "market_cap_usd": 1_200_000_000_000.0,
    "volume_24h_usd": 30_000_000_000.0,
    "rank": 1,
    "ath_usd": 73000.0,
    "circulating_supply": 19_000_000.0,
    "volume_mcap_ratio": 0.025,
    "price_velocity": 0.0,
    "ath_distance_pct": 17.8,
    "fundamental_score": 0.75,
    "opportunity_score": 0.75,
    "token_category": "l1",
}

_RESULT_PEPE: dict[str, object] = {
    "coingecko_id": "pepe",
    "symbol": "PEPE",
    "name": "Pepe",
    "price_usd": 0.00001,
    "market_cap_usd": 5_000_000_000.0,
    "volume_24h_usd": 500_000_000.0,
    "rank": 30,
    "ath_usd": 0.00002,
    "circulating_supply": 420_690_000_000_000.0,
    "volume_mcap_ratio": 0.1,
    "price_velocity": 5.0,
    "ath_distance_pct": 50.0,
    "fundamental_score": 0.30,
    "opportunity_score": 0.21,
    "token_category": "memecoin",
}

_RESULT_BTC_NO_CATEGORY: dict[str, object] = {
    **_RESULT_BTC,
    "token_category": None,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCategoryPersistence:
    """_persist_results must write token_category to Token.category."""

    @pytest.mark.asyncio
    async def test_persist_results_sets_category_on_new_token(
        self, async_session: AsyncSession
    ) -> None:
        """New token must have its category persisted from pipeline result."""
        from app.scheduler.jobs import _persist_results

        await _persist_results([_RESULT_BTC], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category == "l1"

    @pytest.mark.asyncio
    async def test_persist_results_sets_memecoin_category(
        self, async_session: AsyncSession
    ) -> None:
        """Memecoin category must be persisted correctly."""
        from app.scheduler.jobs import _persist_results

        await _persist_results([_RESULT_PEPE], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category == "memecoin"

    @pytest.mark.asyncio
    async def test_persist_results_leaves_category_none_when_not_provided(
        self, async_session: AsyncSession
    ) -> None:
        """Token without token_category in pipeline result keeps category=None."""
        from app.scheduler.jobs import _persist_results

        result_no_cat: dict[str, object] = {**_RESULT_BTC, "coingecko_id": "bitcoin2"}
        result_no_cat.pop("token_category", None)
        # Use a different symbol so it doesn't clash
        result_no_cat["symbol"] = "BTC2"

        await _persist_results([result_no_cat], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category is None

    @pytest.mark.asyncio
    async def test_persist_results_backfills_category_on_existing_token(
        self, async_session: AsyncSession
    ) -> None:
        """Existing token with null category gets backfilled on next pipeline run."""
        from app.scheduler.jobs import _persist_results

        # First run: no category
        await _persist_results([_RESULT_BTC_NO_CATEGORY], session=async_session)
        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category is None

        # Second run: category available
        await _persist_results([_RESULT_BTC], session=async_session)
        await async_session.refresh(token)
        assert token.category == "l1"

    @pytest.mark.asyncio
    async def test_persist_results_updates_real_category_over_existing(
        self, async_session: AsyncSession
    ) -> None:
        """When CoinGecko reclassifies a token, the category should be updated."""
        from app.scheduler.jobs import _persist_results

        # First run: l1
        await _persist_results([_RESULT_BTC], session=async_session)

        # Second run: pipeline now says 'infrastructure' (CoinGecko reclassified)
        changed = {**_RESULT_BTC, "token_category": "infrastructure"}
        await _persist_results([changed], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        # Category should be updated to the new real classification
        assert token.category == "infrastructure"

    @pytest.mark.asyncio
    async def test_persist_results_does_not_downgrade_to_unknown(
        self, async_session: AsyncSession
    ) -> None:
        """Once a token has a real category, 'unknown' should not overwrite it."""
        from app.scheduler.jobs import _persist_results

        # First run: l1
        await _persist_results([_RESULT_BTC], session=async_session)

        # Second run: category detection failed → unknown
        changed = {**_RESULT_BTC, "token_category": "unknown"}
        await _persist_results([changed], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        # Should NOT downgrade from l1 to unknown
        assert token.category == "l1"

    @pytest.mark.asyncio
    async def test_persist_results_multiple_tokens_with_categories(
        self, async_session: AsyncSession
    ) -> None:
        """Multiple tokens in one batch get correct categories."""
        from app.scheduler.jobs import _persist_results

        await _persist_results([_RESULT_BTC, _RESULT_PEPE], session=async_session)

        tokens = (await async_session.execute(select(Token))).scalars().all()
        categories = {t.symbol: t.category for t in tokens}
        assert categories == {"BTC": "l1", "PEPE": "memecoin"}
