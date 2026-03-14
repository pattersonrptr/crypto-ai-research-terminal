#!/usr/bin/env python3
"""Seed the database with historical OHLCV candle data for backtesting.

Fetches daily OHLCV data from the CoinGecko public API
(``/coins/{id}/market_chart/range``) and persists it in the
``historical_candles`` table.  All inserts are idempotent — duplicate rows
(same symbol + timestamp) are silently ignored via ``ON CONFLICT DO NOTHING``.

The script covers the three market cycles defined by
``app.backtesting.data_loader.CycleLabel``:

  - BULL         2017-01-01 → 2018-01-31
  - BEAR         2018-02-01 → 2020-03-31
  - ACCUMULATION 2020-04-01 → 2021-11-30

Usage (from project root with venv activated)::

    python -m scripts.seed_historical_data

Environment variables (loaded from .env via pydantic-settings):
    DATABASE_URL  — async PostgreSQL URL (postgresql+asyncpg://...)
    COINGECKO_API_KEY — optional; required for CoinGecko Pro endpoints
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Path setup — allow running as ``python -m scripts.seed_historical_data``
# from the project root as well as directly from the backend directory.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings  # noqa: E402

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Tokens to seed  (symbol → CoinGecko ID)
# ---------------------------------------------------------------------------

TOKENS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "ARB": "arbitrum",
}

# ---------------------------------------------------------------------------
# Cycle date ranges  (start inclusive, end inclusive) as UTC unix timestamps
# ---------------------------------------------------------------------------

_CYCLES: list[tuple[datetime, datetime]] = [
    # BULL
    (datetime(2017, 1, 1, tzinfo=UTC), datetime(2018, 1, 31, tzinfo=UTC)),
    # BEAR
    (datetime(2018, 2, 1, tzinfo=UTC), datetime(2020, 3, 31, tzinfo=UTC)),
    # ACCUMULATION
    (datetime(2020, 4, 1, tzinfo=UTC), datetime(2021, 11, 30, tzinfo=UTC)),
]

_COINGECKO_BASE = "https://api.coingecko.com/api/v3"


# ---------------------------------------------------------------------------
# Pure functions (testable without I/O)
# ---------------------------------------------------------------------------


def parse_market_chart_response(
    symbol: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert a raw CoinGecko market_chart/range payload to candle dicts.

    CoinGecko returns three parallel lists:
      - ``prices``        — [[ts_ms, price], ...]
      - ``total_volumes`` — [[ts_ms, volume], ...]
      - ``market_caps``   — [[ts_ms, market_cap], ...]

    We treat each ``price`` entry as the *close* price of that daily candle.
    Because the API does not provide true OHLC data at the free tier, we use
    the close price for all of open / high / low / close.  The backtesting
    engine only uses ``close`` for signal generation, so this is acceptable.

    Args:
        symbol: Token ticker (e.g. ``"BTC"``).
        payload: Raw JSON dict from the CoinGecko endpoint.

    Returns:
        List of candle dicts ready for ``insert_candles()``.
    """
    prices: list[list[float]] = payload.get("prices", [])
    volumes: list[list[float]] = payload.get("total_volumes", [])
    market_caps: list[list[float]] = payload.get("market_caps", [])

    if not prices:
        return []

    candles: list[dict[str, Any]] = []
    for i, (ts_ms, price) in enumerate(prices):
        timestamp = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        volume = volumes[i][1] if i < len(volumes) else 0.0
        market_cap: float | None = market_caps[i][1] if i < len(market_caps) else None

        candles.append(
            {
                "symbol": symbol,
                "timestamp": timestamp,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume_usd": volume,
                "market_cap_usd": market_cap,
            }
        )

    return candles


# ---------------------------------------------------------------------------
# I/O functions
# ---------------------------------------------------------------------------


async def fetch_ohlcv(
    client: httpx.AsyncClient,
    coingecko_id: str,
    from_ts: int,
    to_ts: int,
    api_key: str = "",
) -> dict[str, Any]:
    """Fetch OHLCV data from CoinGecko market_chart/range endpoint.

    Args:
        client: An ``httpx.AsyncClient`` already configured with the base URL.
        coingecko_id: CoinGecko coin ID (e.g. ``"bitcoin"``).
        from_ts: Start of range as Unix timestamp (seconds).
        to_ts: End of range as Unix timestamp (seconds).
        api_key: Optional CoinGecko Pro API key.

    Returns:
        Raw JSON dict with ``prices``, ``total_volumes`` and ``market_caps`` lists.

    Raises:
        httpx.HTTPStatusError: On any non-2xx HTTP response.
    """
    params: dict[str, Any] = {
        "vs_currency": "usd",
        "from": from_ts,
        "to": to_ts,
    }
    if api_key:
        params["x_cg_pro_api_key"] = api_key

    path = f"/coins/{coingecko_id}/market_chart/range"
    logger.debug(
        "seed.fetch_ohlcv.request",
        coingecko_id=coingecko_id,
        from_ts=from_ts,
        to_ts=to_ts,
    )

    response = await client.get(path, params=params)
    response.raise_for_status()

    logger.debug(
        "seed.fetch_ohlcv.ok",
        coingecko_id=coingecko_id,
        status=response.status_code,
    )
    result: dict[str, Any] = response.json()
    return result


async def insert_candles(
    session: AsyncSession,
    candles: list[dict[str, Any]],
) -> None:
    """Insert candle rows idempotently (ON CONFLICT DO NOTHING).

    Uses raw SQL ``INSERT OR IGNORE`` for SQLite (tests) and
    ``INSERT … ON CONFLICT DO NOTHING`` for PostgreSQL (production).
    The dialect is detected from the engine URL at runtime.

    Args:
        session: An open ``AsyncSession``.
        candles: List of candle dicts as returned by ``parse_market_chart_response()``.
    """
    if not candles:
        return

    dialect = session.get_bind().dialect.name

    for candle in candles:
        if dialect == "sqlite":
            stmt = text(
                "INSERT OR IGNORE INTO historical_candles "
                "(symbol, timestamp, open, high, low, close, volume_usd, market_cap_usd) "
                "VALUES "
                "(:symbol, :timestamp, :open, :high, :low, :close, :volume_usd, :market_cap_usd)"
            )
        else:
            stmt = text(
                "INSERT INTO historical_candles "
                "(symbol, timestamp, open, high, low, close, volume_usd, market_cap_usd) "
                "VALUES "
                "(:symbol, :timestamp, :open, :high, :low, :close, :volume_usd, :market_cap_usd) "
                "ON CONFLICT (symbol, timestamp) DO NOTHING"
            )

        await session.execute(stmt, candle)


async def seed_symbol(
    client: httpx.AsyncClient,
    session: AsyncSession,
    symbol: str,
    coingecko_id: str,
    from_ts: int,
    to_ts: int,
    api_key: str = "",
) -> None:
    """Fetch, parse and insert candles for a single token + time range.

    Errors from the HTTP layer are caught, logged and swallowed so that
    a single failing symbol does not abort the entire seed run.

    Args:
        client: Configured ``httpx.AsyncClient``.
        session: Open ``AsyncSession``.
        symbol: Token ticker (e.g. ``"BTC"``).
        coingecko_id: CoinGecko coin ID (e.g. ``"bitcoin"``).
        from_ts: Range start as Unix timestamp (seconds).
        to_ts: Range end as Unix timestamp (seconds).
        api_key: Optional CoinGecko Pro API key.
    """
    try:
        payload = await fetch_ohlcv(client, coingecko_id, from_ts, to_ts, api_key)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "seed.fetch_ohlcv.http_error",
            symbol=symbol,
            status=exc.response.status_code,
        )
        return
    except Exception as exc:
        logger.error(
            "seed.fetch_ohlcv.unexpected_error",
            symbol=symbol,
            error=str(exc),
        )
        return

    candles = parse_market_chart_response(symbol, payload)
    logger.info("seed.inserting_candles", symbol=symbol, count=len(candles))
    await insert_candles(session, candles)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the full seed process for all tokens and all cycles."""
    logger.info("seed_historical_data.start", tokens=list(TOKENS.keys()), cycles=len(_CYCLES))

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    api_key: str = getattr(settings, "coingecko_api_key", "")

    async with (
        httpx.AsyncClient(base_url=_COINGECKO_BASE, timeout=60.0) as client,
        session_factory() as session,
    ):
        for start_dt, end_dt in _CYCLES:
            from_ts = int(start_dt.timestamp())
            to_ts = int(end_dt.timestamp())
            logger.info(
                "seed.cycle.start",
                cycle_start=start_dt.date().isoformat(),
                cycle_end=end_dt.date().isoformat(),
            )

            for symbol, coingecko_id in TOKENS.items():
                await seed_symbol(
                    client=client,
                    session=session,
                    symbol=symbol,
                    coingecko_id=coingecko_id,
                    from_ts=from_ts,
                    to_ts=to_ts,
                    api_key=api_key,
                )
                await session.commit()

            logger.info(
                "seed.cycle.done",
                cycle_start=start_dt.date().isoformat(),
                cycle_end=end_dt.date().isoformat(),
            )

    await engine.dispose()
    logger.info("seed_historical_data.done")


if __name__ == "__main__":
    asyncio.run(main())
