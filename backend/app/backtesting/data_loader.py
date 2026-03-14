"""Data loader — provides historical OHLCV candle data for backtesting.

Supports loading by symbol, by date range, or by pre-defined market cycle
labels (BULL / BEAR / ACCUMULATION).  Data is injected at construction time,
keeping the module decoupled from any specific data source (DB, CSV, API).

This module is part of the Backtesting Engine (Phase 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Pre-defined cycle date ranges (start inclusive, end inclusive)
# ---------------------------------------------------------------------------

_CYCLE_RANGES: dict[str, tuple[datetime, datetime]] = {
    "bull": (
        datetime(2017, 1, 1, tzinfo=UTC),
        datetime(2018, 1, 31, tzinfo=UTC),
    ),
    "bear": (
        datetime(2018, 2, 1, tzinfo=UTC),
        datetime(2020, 3, 31, tzinfo=UTC),
    ),
    "accumulation": (
        datetime(2020, 4, 1, tzinfo=UTC),
        datetime(2021, 11, 30, tzinfo=UTC),
    ),
}


# ---------------------------------------------------------------------------
# Data classes / enums
# ---------------------------------------------------------------------------


class CycleLabel(str, Enum):
    """Market-cycle labels used to select a pre-defined date range."""

    BULL = "bull"
    BEAR = "bear"
    ACCUMULATION = "accumulation"


@dataclass
class HistoricalCandle:
    """A single OHLCV candle for a given token.

    Args:
        symbol: Token ticker (e.g. "BTC").
        timestamp: UTC datetime of the candle open.
        open: Opening price in USD.
        high: Highest price in USD during the period.
        low: Lowest price in USD during the period.
        close: Closing price in USD.
        volume_usd: Trading volume in USD during the period.
        market_cap_usd: Optional market cap in USD at candle close.
    """

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume_usd: float
    market_cap_usd: float | None = None

    @property
    def price_change_pct(self) -> float:
        """Return the percentage price change from open to close.

        Returns 0.0 when ``open`` is zero to avoid division by zero.
        """
        if self.open == 0.0:
            return 0.0
        return (self.close - self.open) / self.open * 100.0


# ---------------------------------------------------------------------------
# DataLoader
# ---------------------------------------------------------------------------


@dataclass
class DataLoader:
    """In-memory store and query interface for historical candle data.

    Candles are injected at construction time so the loader remains agnostic
    of the data source (PostgreSQL, CSV, external API, etc.).

    Usage::

        loader = DataLoader(candles=my_candles)
        btc = loader.load_symbol("BTC")
        bull_candles = loader.load_cycle("BTC", CycleLabel.BULL)
    """

    candles: list[HistoricalCandle] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def load_symbol(self, symbol: str) -> list[HistoricalCandle]:
        """Return all candles for *symbol*, sorted ascending by timestamp.

        Args:
            symbol: Token ticker to filter on.

        Returns:
            Sorted list of :class:`HistoricalCandle` objects (may be empty).
        """
        result = [c for c in self.candles if c.symbol == symbol]
        result.sort(key=lambda c: c.timestamp)
        return result

    def filter_by_date_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[HistoricalCandle]:
        """Return candles for *symbol* within [*start*, *end*] inclusive.

        Args:
            symbol: Token ticker to filter on.
            start: Start of the date range (inclusive).
            end: End of the date range (inclusive).

        Returns:
            Sorted list of matching :class:`HistoricalCandle` objects.
        """
        result = [c for c in self.candles if c.symbol == symbol and start <= c.timestamp <= end]
        result.sort(key=lambda c: c.timestamp)
        return result

    def load_cycle(
        self,
        symbol: str,
        cycle: CycleLabel,
    ) -> list[HistoricalCandle]:
        """Return candles for *symbol* within a pre-defined market cycle range.

        Args:
            symbol: Token ticker to filter on.
            cycle: One of :class:`CycleLabel` (BULL, BEAR, ACCUMULATION).

        Returns:
            Sorted list of matching :class:`HistoricalCandle` objects.
        """
        start, end = _CYCLE_RANGES[cycle.value]
        result = self.filter_by_date_range(symbol, start, end)
        logger.info(
            "data_loader.load_cycle",
            symbol=symbol,
            cycle=cycle.value,
            n_candles=len(result),
        )
        return result

    def available_symbols(self) -> list[str]:
        """Return a sorted list of distinct token symbols in the dataset."""
        return sorted({c.symbol for c in self.candles})

    def candle_count(self) -> int:
        """Return the total number of candles in the dataset."""
        return len(self.candles)
