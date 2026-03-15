"""TDD tests for _persist_results — real DB persistence of pipeline output.

DB calls use an in-memory SQLite async engine so tests run without PostgreSQL.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from tests.conftest_helpers import create_sqlite_tables

# ---------------------------------------------------------------------------
# Fixtures — in-memory async SQLite engine (no live PostgreSQL required)
# ---------------------------------------------------------------------------


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
}

_RESULT_ETH: dict[str, object] = {
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
    "fundamental_score": 0.82,
    "opportunity_score": 0.82,
}


# ---------------------------------------------------------------------------
# Tests — _persist_results
# ---------------------------------------------------------------------------


class TestPersistResults:
    """Tests for _persist_results writing to tokens, token_scores, market_data."""

    @pytest.mark.asyncio
    async def test_persist_results_creates_token_row(self, async_session: AsyncSession) -> None:
        """_persist_results must insert a Token row for each result."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)

        rows = (await async_session.execute(select(Token))).scalars().all()
        assert len(rows) == 1
        assert rows[0].symbol == "BTC"
        assert rows[0].name == "Bitcoin"
        assert rows[0].coingecko_id == "bitcoin"

    @pytest.mark.asyncio
    async def test_persist_results_creates_token_score_row(
        self, async_session: AsyncSession
    ) -> None:
        """_persist_results must insert a TokenScore for each result."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)

        rows = (await async_session.execute(select(TokenScore))).scalars().all()
        assert len(rows) == 1
        assert rows[0].fundamental_score == pytest.approx(0.75)
        assert rows[0].opportunity_score == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_persist_results_creates_market_data_row(
        self, async_session: AsyncSession
    ) -> None:
        """_persist_results must insert a MarketData snapshot for each result."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)

        rows = (await async_session.execute(select(MarketData))).scalars().all()
        assert len(rows) == 1
        assert rows[0].price_usd == pytest.approx(60000.0)
        assert rows[0].market_cap_usd == pytest.approx(1_200_000_000_000.0)
        assert rows[0].volume_24h_usd == pytest.approx(30_000_000_000.0)
        assert rows[0].rank == 1

    @pytest.mark.asyncio
    async def test_persist_results_multiple_tokens(self, async_session: AsyncSession) -> None:
        """_persist_results must handle a list of multiple results."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC, _RESULT_ETH], session=async_session)

        tokens = (await async_session.execute(select(Token))).scalars().all()
        scores = (await async_session.execute(select(TokenScore))).scalars().all()
        market = (await async_session.execute(select(MarketData))).scalars().all()
        assert len(tokens) == 2
        assert len(scores) == 2
        assert len(market) == 2

    @pytest.mark.asyncio
    async def test_persist_results_upserts_existing_token(
        self, async_session: AsyncSession
    ) -> None:
        """Running _persist_results twice for the same token must not duplicate it."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)
        await _persist_results([_RESULT_BTC], session=async_session)

        tokens = (await async_session.execute(select(Token))).scalars().all()
        assert len(tokens) == 1  # no duplicate

        # But should have 2 score snapshots (one per run)
        scores = (await async_session.execute(select(TokenScore))).scalars().all()
        assert len(scores) == 2

    @pytest.mark.asyncio
    async def test_persist_results_links_score_to_token(self, async_session: AsyncSession) -> None:
        """TokenScore.token_id must reference the correct Token.id."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        score = (await async_session.execute(select(TokenScore))).scalars().first()
        assert token is not None
        assert score is not None
        assert score.token_id == token.id

    @pytest.mark.asyncio
    async def test_persist_results_links_market_data_to_token(
        self, async_session: AsyncSession
    ) -> None:
        """MarketData.token_id must reference the correct Token.id."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([_RESULT_BTC], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        md = (await async_session.execute(select(MarketData))).scalars().first()
        assert token is not None
        assert md is not None
        assert md.token_id == token.id

    @pytest.mark.asyncio
    async def test_persist_results_empty_list_is_noop(self, async_session: AsyncSession) -> None:
        """_persist_results with empty list must not crash."""
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        await _persist_results([], session=async_session)

        tokens = (await async_session.execute(select(Token))).scalars().all()
        assert len(tokens) == 0

    @pytest.mark.asyncio
    async def test_persist_results_skips_duplicate_symbol_different_coingecko_id(
        self, async_session: AsyncSession
    ) -> None:
        """Two items with the same symbol but different coingecko_id must not crash.

        The first item wins; the second is silently skipped (scores + market_data
        are NOT created for the duplicate).
        """
        from app.scheduler.jobs import _persist_results  # noqa: PLC0415

        dup_a: dict[str, object] = {
            **_RESULT_BTC,
            "coingecko_id": "wrapped-bitcoin",
            "symbol": "BTC",
            "name": "Wrapped Bitcoin",
        }

        await _persist_results([_RESULT_BTC, dup_a], session=async_session)

        tokens = (await async_session.execute(select(Token))).scalars().all()
        assert len(tokens) == 1
        assert tokens[0].coingecko_id == "bitcoin"  # first one wins
