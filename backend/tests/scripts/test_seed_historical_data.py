"""Tests for seed_historical_data script.

All HTTP calls are mocked with respx — no real network requests are made.
DB calls use an in-memory SQLite async engine.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.historical_candle import HistoricalCandle
from tests.conftest_helpers import create_sqlite_tables

# ---------------------------------------------------------------------------
# Helpers — CoinGecko market_chart/range response shape
# ---------------------------------------------------------------------------

_COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Minimal CoinGecko /coins/{id}/market_chart/range response
# prices: [[ts_ms, price], ...]
# total_volumes: [[ts_ms, volume], ...]
# market_caps: [[ts_ms, market_cap], ...]
_MARKET_CHART_RESPONSE: dict[str, Any] = {
    "prices": [
        [1483228800000, 1000.0],  # 2017-01-01
        [1483315200000, 1050.0],  # 2017-01-02
    ],
    "total_volumes": [
        [1483228800000, 5_000_000.0],
        [1483315200000, 5_200_000.0],
    ],
    "market_caps": [
        [1483228800000, 16_000_000_000.0],
        [1483315200000, 16_500_000_000.0],
    ],
}


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
# Tests — HistoricalCandle model
# ---------------------------------------------------------------------------


class TestHistoricalCandleModel:
    """HistoricalCandle ORM model has correct structure and constraints."""

    def test_historical_candle_model_has_expected_tablename(self) -> None:
        assert HistoricalCandle.__tablename__ == "historical_candles"

    def test_historical_candle_model_repr_contains_symbol(self) -> None:
        candle = HistoricalCandle(
            symbol="BTC",
            timestamp=datetime(2017, 1, 1, tzinfo=UTC),
            open=1000.0,
            high=1100.0,
            low=950.0,
            close=1050.0,
            volume_usd=5_000_000.0,
        )
        assert "BTC" in repr(candle)

    def test_historical_candle_model_market_cap_optional(self) -> None:
        candle = HistoricalCandle(
            symbol="ETH",
            timestamp=datetime(2017, 1, 1, tzinfo=UTC),
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume_usd=1_000_000.0,
            market_cap_usd=None,
        )
        assert candle.market_cap_usd is None


# ---------------------------------------------------------------------------
# Tests — parse_market_chart_response
# ---------------------------------------------------------------------------


class TestParseMarketChartResponse:
    """parse_market_chart_response converts raw CoinGecko payload to candle dicts."""

    def test_parse_market_chart_response_returns_list(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        assert isinstance(result, list)

    def test_parse_market_chart_response_length_matches_prices(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        assert len(result) == len(_MARKET_CHART_RESPONSE["prices"])

    def test_parse_market_chart_response_candle_has_required_keys(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        candle = result[0]
        expected_keys = (
            "symbol",
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume_usd",
            "market_cap_usd",
        )
        for key in expected_keys:
            assert key in candle, f"Missing key: {key}"

    def test_parse_market_chart_response_symbol_is_preserved(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("ETH", _MARKET_CHART_RESPONSE)
        assert all(c["symbol"] == "ETH" for c in result)

    def test_parse_market_chart_response_timestamp_is_utc(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        ts: datetime = result[0]["timestamp"]
        assert ts.tzinfo is not None
        assert ts == datetime(2017, 1, 1, tzinfo=UTC)

    def test_parse_market_chart_response_close_comes_from_prices(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        assert result[0]["close"] == 1000.0
        assert result[1]["close"] == 1050.0

    def test_parse_market_chart_response_volume_usd_correct(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        assert result[0]["volume_usd"] == 5_000_000.0

    def test_parse_market_chart_response_market_cap_usd_correct(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response("BTC", _MARKET_CHART_RESPONSE)
        assert result[0]["market_cap_usd"] == 16_000_000_000.0

    def test_parse_market_chart_response_empty_payload_returns_empty_list(self) -> None:
        from scripts.seed_historical_data import parse_market_chart_response

        result = parse_market_chart_response(
            "BTC",
            {"prices": [], "total_volumes": [], "market_caps": []},
        )
        assert result == []


# ---------------------------------------------------------------------------
# Tests — fetch_ohlcv (HTTP layer)
# ---------------------------------------------------------------------------


class TestFetchOhlcv:
    """fetch_ohlcv calls the CoinGecko market_chart/range endpoint correctly."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_calls_correct_endpoint(self) -> None:
        from scripts.seed_historical_data import fetch_ohlcv

        route = respx.get(f"{_COINGECKO_BASE}/coins/bitcoin/market_chart/range").mock(
            return_value=httpx.Response(200, json=_MARKET_CHART_RESPONSE)
        )

        async with httpx.AsyncClient(base_url=_COINGECKO_BASE) as client:
            result = await fetch_ohlcv(
                client,
                coingecko_id="bitcoin",
                from_ts=1483228800,
                to_ts=1483315200,
            )

        assert route.called
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_returns_raw_payload(self) -> None:
        from scripts.seed_historical_data import fetch_ohlcv

        respx.get(f"{_COINGECKO_BASE}/coins/bitcoin/market_chart/range").mock(
            return_value=httpx.Response(200, json=_MARKET_CHART_RESPONSE)
        )

        async with httpx.AsyncClient(base_url=_COINGECKO_BASE) as client:
            result = await fetch_ohlcv(
                client,
                coingecko_id="bitcoin",
                from_ts=1483228800,
                to_ts=1483315200,
            )

        assert "prices" in result
        assert "total_volumes" in result
        assert "market_caps" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_ohlcv_raises_on_http_error(self) -> None:
        from scripts.seed_historical_data import fetch_ohlcv

        respx.get(f"{_COINGECKO_BASE}/coins/bitcoin/market_chart/range").mock(
            return_value=httpx.Response(429)
        )

        async with httpx.AsyncClient(base_url=_COINGECKO_BASE) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_ohlcv(
                    client,
                    coingecko_id="bitcoin",
                    from_ts=1483228800,
                    to_ts=1483315200,
                )


# ---------------------------------------------------------------------------
# Tests — insert_candles (DB layer)
# ---------------------------------------------------------------------------


class TestInsertCandles:
    """insert_candles persists candles idempotently (ON CONFLICT DO NOTHING)."""

    @pytest.mark.asyncio
    async def test_insert_candles_persists_rows(self, async_session: AsyncSession) -> None:
        from scripts.seed_historical_data import insert_candles

        candles = [
            {
                "symbol": "BTC",
                "timestamp": datetime(2017, 1, 1, tzinfo=UTC),
                "open": 1000.0,
                "high": 1100.0,
                "low": 950.0,
                "close": 1050.0,
                "volume_usd": 5_000_000.0,
                "market_cap_usd": 16_000_000_000.0,
            }
        ]
        await insert_candles(async_session, candles)
        await async_session.commit()

        result = await async_session.execute(
            select(HistoricalCandle).where(HistoricalCandle.symbol == "BTC")
        )
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].close == 1050.0

    @pytest.mark.asyncio
    async def test_insert_candles_idempotent_on_duplicate(
        self, async_session: AsyncSession
    ) -> None:
        from scripts.seed_historical_data import insert_candles

        candle = {
            "symbol": "BTC",
            "timestamp": datetime(2017, 1, 2, tzinfo=UTC),
            "open": 1020.0,
            "high": 1060.0,
            "low": 1000.0,
            "close": 1040.0,
            "volume_usd": 4_800_000.0,
            "market_cap_usd": 16_200_000_000.0,
        }
        await insert_candles(async_session, [candle])
        await async_session.commit()
        # Insert again — must not raise or duplicate
        await insert_candles(async_session, [candle])
        await async_session.commit()

        result = await async_session.execute(
            select(HistoricalCandle).where(HistoricalCandle.symbol == "BTC")
        )
        rows = result.scalars().all()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_insert_candles_multiple_symbols(self, async_session: AsyncSession) -> None:
        from scripts.seed_historical_data import insert_candles

        candles = [
            {
                "symbol": "BTC",
                "timestamp": datetime(2017, 1, 3, tzinfo=UTC),
                "open": 1000.0,
                "high": 1100.0,
                "low": 950.0,
                "close": 1050.0,
                "volume_usd": 5_000_000.0,
                "market_cap_usd": None,
            },
            {
                "symbol": "ETH",
                "timestamp": datetime(2017, 1, 3, tzinfo=UTC),
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "volume_usd": 1_000_000.0,
                "market_cap_usd": None,
            },
        ]
        await insert_candles(async_session, candles)
        await async_session.commit()

        result = await async_session.execute(select(HistoricalCandle))
        rows = result.scalars().all()
        symbols = {r.symbol for r in rows}
        assert "BTC" in symbols
        assert "ETH" in symbols

    @pytest.mark.asyncio
    async def test_insert_candles_empty_list_is_noop(self, async_session: AsyncSession) -> None:
        from scripts.seed_historical_data import insert_candles

        # Should not raise
        await insert_candles(async_session, [])
        await async_session.commit()

        result = await async_session.execute(select(HistoricalCandle))
        rows = result.scalars().all()
        assert rows == []


# ---------------------------------------------------------------------------
# Tests — seed_symbol (orchestration per token)
# ---------------------------------------------------------------------------


class TestSeedSymbol:
    """seed_symbol orchestrates fetch + parse + insert for one token."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_seed_symbol_inserts_candles_for_given_symbol(
        self, async_session: AsyncSession
    ) -> None:
        from scripts.seed_historical_data import seed_symbol

        respx.get(f"{_COINGECKO_BASE}/coins/bitcoin/market_chart/range").mock(
            return_value=httpx.Response(200, json=_MARKET_CHART_RESPONSE)
        )

        async with httpx.AsyncClient(base_url=_COINGECKO_BASE) as client:
            await seed_symbol(
                client=client,
                session=async_session,
                symbol="BTC",
                coingecko_id="bitcoin",
                from_ts=1483228800,
                to_ts=1483315200,
            )
        await async_session.commit()

        result = await async_session.execute(
            select(HistoricalCandle).where(HistoricalCandle.symbol == "BTC")
        )
        rows = result.scalars().all()
        assert len(rows) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_seed_symbol_logs_and_continues_on_http_error(
        self, async_session: AsyncSession
    ) -> None:
        from scripts.seed_historical_data import seed_symbol

        respx.get(f"{_COINGECKO_BASE}/coins/unknown-coin/market_chart/range").mock(
            return_value=httpx.Response(404)
        )

        # Should NOT raise — errors are swallowed and logged
        async with httpx.AsyncClient(base_url=_COINGECKO_BASE) as client:
            await seed_symbol(
                client=client,
                session=async_session,
                symbol="UNK",
                coingecko_id="unknown-coin",
                from_ts=1483228800,
                to_ts=1483315200,
            )

        result = await async_session.execute(select(HistoricalCandle))
        rows = result.scalars().all()
        assert rows == []
