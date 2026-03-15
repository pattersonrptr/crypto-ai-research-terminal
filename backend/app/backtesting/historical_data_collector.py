"""Historical data collector — fetches and formats CoinGecko market data.

Converts raw CoinGecko ``/coins/{id}/market_chart/range`` responses into
snapshot dictionaries suitable for the ``historical_snapshots`` table.

This module provides **pure functions** for parsing and transforming data.
The actual HTTP fetching is handled by ``seed_historical_data.py`` or
the existing ``CoinGeckoCollector``.

This module is part of Phase 12 — Backtesting Validation.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Tokens covered by the validation dataset
# ---------------------------------------------------------------------------

VALIDATION_TOKENS: dict[str, str] = {
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
    "DOT": "polkadot",
    "ADA": "cardano",
    "ATOM": "cosmos",
    "NEAR": "near",
    "FTM": "fantom",
}


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------


def parse_market_chart_to_snapshots(
    symbol: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert a CoinGecko market_chart/range response to snapshot dicts.

    CoinGecko returns parallel lists:
      - ``prices``        — [[ts_ms, price], ...]
      - ``total_volumes`` — [[ts_ms, volume], ...]
      - ``market_caps``   — [[ts_ms, market_cap], ...]

    Each data point is converted to a daily snapshot. Multiple data points
    on the same calendar day are deduplicated (last value wins).

    Args:
        symbol: Token ticker (e.g. ``"BTC"``).
        payload: Raw JSON dict from CoinGecko.

    Returns:
        List of snapshot dicts sorted by snapshot_date ascending.
    """
    prices: list[list[float]] = payload.get("prices", [])
    volumes: list[list[float]] = payload.get("total_volumes", [])
    market_caps: list[list[float]] = payload.get("market_caps", [])

    if not prices:
        return []

    # Build per-day snapshots (last value per day wins)
    day_map: dict[date, dict[str, Any]] = {}

    for i, (ts_ms, price) in enumerate(prices):
        snap_date = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC).date()
        volume = volumes[i][1] if i < len(volumes) else 0.0
        market_cap = market_caps[i][1] if i < len(market_caps) else 0.0

        day_map[snap_date] = {
            "symbol": symbol,
            "snapshot_date": snap_date,
            "price_usd": price,
            "market_cap_usd": market_cap,
            "volume_usd": volume,
        }

    result = list(day_map.values())
    result.sort(key=lambda s: s["snapshot_date"])

    logger.debug(
        "historical_data_collector.parsed",
        symbol=symbol,
        n_snapshots=len(result),
    )
    return result


# ---------------------------------------------------------------------------
# Monthly snapshot builder
# ---------------------------------------------------------------------------


def build_monthly_snapshots(
    daily_snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Select one snapshot per month (closest to 1st) from a daily series.

    For each unique (year, month) in the dataset, pick the snapshot
    with the earliest date in that month.

    Args:
        daily_snapshots: List of snapshot dicts with ``snapshot_date`` keys.

    Returns:
        List of monthly snapshot dicts, sorted by date ascending.
    """
    if not daily_snapshots:
        return []

    # Group by (year, month)
    month_map: dict[tuple[int, int], dict[str, Any]] = {}

    for snap in daily_snapshots:
        sd: date = snap["snapshot_date"]
        key = (sd.year, sd.month)
        if key not in month_map or sd < month_map[key]["snapshot_date"]:
            month_map[key] = snap

    result = list(month_map.values())
    result.sort(key=lambda s: s["snapshot_date"])

    logger.debug(
        "historical_data_collector.monthly_built",
        n_months=len(result),
    )
    return result
