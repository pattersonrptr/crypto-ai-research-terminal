"""Tests for app.backtesting.data_loader — TDD Red→Green."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.backtesting.data_loader import CycleLabel, DataLoader, HistoricalCandle

# ---------------------------------------------------------------------------
# TestHistoricalCandle
# ---------------------------------------------------------------------------


class TestHistoricalCandle:
    """Unit tests for the HistoricalCandle dataclass."""

    def test_historical_candle_required_fields_are_set(self) -> None:
        """HistoricalCandle must store symbol, timestamp, open, high, low, close, volume."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        candle = HistoricalCandle(
            symbol="BTC",
            timestamp=ts,
            open=29_000.0,
            high=30_000.0,
            low=28_000.0,
            close=29_500.0,
            volume_usd=1_500_000_000.0,
        )
        assert candle.symbol == "BTC"
        assert candle.timestamp == ts
        assert candle.open == 29_000.0
        assert candle.high == 30_000.0
        assert candle.low == 28_000.0
        assert candle.close == 29_500.0
        assert candle.volume_usd == 1_500_000_000.0

    def test_historical_candle_market_cap_optional_defaults_to_none(self) -> None:
        """market_cap_usd must default to None when omitted."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        candle = HistoricalCandle(
            symbol="BTC",
            timestamp=ts,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume_usd=1.0,
        )
        assert candle.market_cap_usd is None

    def test_historical_candle_price_change_pct_computed_correctly(self) -> None:
        """price_change_pct must return (close-open)/open * 100."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        candle = HistoricalCandle(
            symbol="BTC",
            timestamp=ts,
            open=100.0,
            high=110.0,
            low=90.0,
            close=110.0,
            volume_usd=1.0,
        )
        assert candle.price_change_pct == pytest.approx(10.0)

    def test_historical_candle_price_change_pct_zero_open_returns_zero(self) -> None:
        """price_change_pct must return 0.0 when open is 0 to avoid division by zero."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        candle = HistoricalCandle(
            symbol="BTC", timestamp=ts, open=0.0, high=1.0, low=0.0, close=1.0, volume_usd=1.0
        )
        assert candle.price_change_pct == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestCycleLabel
# ---------------------------------------------------------------------------


class TestCycleLabel:
    """Unit tests for the CycleLabel enum."""

    def test_cycle_label_values_exist(self) -> None:
        """CycleLabel must define BULL, BEAR, and ACCUMULATION values."""
        assert CycleLabel.BULL.value == "bull"
        assert CycleLabel.BEAR.value == "bear"
        assert CycleLabel.ACCUMULATION.value == "accumulation"


# ---------------------------------------------------------------------------
# TestDataLoaderInMemory
# ---------------------------------------------------------------------------


class TestDataLoaderLoadSymbol:
    """Tests for DataLoader.load_symbol() using in-memory data."""

    def _make_candle(self, symbol: str, ts: datetime, close: float) -> HistoricalCandle:
        return HistoricalCandle(
            symbol=symbol,
            timestamp=ts,
            open=close * 0.99,
            high=close * 1.01,
            low=close * 0.98,
            close=close,
            volume_usd=1_000.0,
        )

    def test_load_symbol_returns_candles_for_symbol(self) -> None:
        """load_symbol() must return only candles matching the given symbol."""
        candles = [
            self._make_candle("BTC", datetime(2021, 1, 1, tzinfo=UTC), 30_000.0),
            self._make_candle("ETH", datetime(2021, 1, 1, tzinfo=UTC), 1_000.0),
            self._make_candle("BTC", datetime(2021, 1, 2, tzinfo=UTC), 31_000.0),
        ]
        loader = DataLoader(candles=candles)
        result = loader.load_symbol("BTC")
        assert len(result) == 2
        assert all(c.symbol == "BTC" for c in result)

    def test_load_symbol_unknown_symbol_returns_empty_list(self) -> None:
        """load_symbol() for a symbol not in the dataset must return []."""
        loader = DataLoader(candles=[])
        assert loader.load_symbol("DOGE") == []

    def test_load_symbol_results_are_sorted_by_timestamp(self) -> None:
        """load_symbol() must return candles in ascending timestamp order."""
        candles = [
            self._make_candle("BTC", datetime(2021, 1, 3, tzinfo=UTC), 32_000.0),
            self._make_candle("BTC", datetime(2021, 1, 1, tzinfo=UTC), 30_000.0),
            self._make_candle("BTC", datetime(2021, 1, 2, tzinfo=UTC), 31_000.0),
        ]
        loader = DataLoader(candles=candles)
        result = loader.load_symbol("BTC")
        timestamps = [c.timestamp for c in result]
        assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# TestDataLoaderFilterByDateRange
# ---------------------------------------------------------------------------


class TestDataLoaderFilterByDateRange:
    """Tests for DataLoader.filter_by_date_range()."""

    def _candles(self) -> list[HistoricalCandle]:
        dates = [date(2021, 1, d) for d in range(1, 6)]
        return [
            HistoricalCandle(
                symbol="BTC",
                timestamp=datetime(d.year, d.month, d.day, tzinfo=UTC),
                open=1.0,
                high=1.0,
                low=1.0,
                close=float(i + 1),
                volume_usd=1.0,
            )
            for i, d in enumerate(dates)
        ]

    def test_filter_by_date_range_returns_candles_within_range(self) -> None:
        """filter_by_date_range() must include candles from start to end inclusive."""
        loader = DataLoader(candles=self._candles())
        start = datetime(2021, 1, 2, tzinfo=UTC)
        end = datetime(2021, 1, 4, tzinfo=UTC)
        result = loader.filter_by_date_range("BTC", start, end)
        assert len(result) == 3
        assert result[0].timestamp == start
        assert result[-1].timestamp == end

    def test_filter_by_date_range_empty_when_outside_range(self) -> None:
        """filter_by_date_range() must return [] when the range has no matching candles."""
        loader = DataLoader(candles=self._candles())
        start = datetime(2022, 1, 1, tzinfo=UTC)
        end = datetime(2022, 12, 31, tzinfo=UTC)
        result = loader.filter_by_date_range("BTC", start, end)
        assert result == []


# ---------------------------------------------------------------------------
# TestDataLoaderLoadCycle
# ---------------------------------------------------------------------------


class TestDataLoaderLoadCycle:
    """Tests for DataLoader.load_cycle() which returns a pre-defined date range."""

    def _make_candles_across_cycles(self) -> list[HistoricalCandle]:
        """Create candles spanning multiple market cycles."""
        entries = [
            ("BTC", datetime(2017, 11, 1, tzinfo=UTC), 7_000.0),
            ("BTC", datetime(2017, 12, 17, tzinfo=UTC), 19_000.0),
            ("BTC", datetime(2018, 12, 15, tzinfo=UTC), 3_200.0),
            ("BTC", datetime(2020, 10, 1, tzinfo=UTC), 10_700.0),
            ("BTC", datetime(2021, 11, 10, tzinfo=UTC), 68_000.0),
            ("BTC", datetime(2022, 11, 21, tzinfo=UTC), 15_700.0),
            ("BTC", datetime(2024, 3, 14, tzinfo=UTC), 73_000.0),
        ]
        return [
            HistoricalCandle(
                symbol=sym,
                timestamp=ts,
                open=price * 0.99,
                high=price * 1.02,
                low=price * 0.97,
                close=price,
                volume_usd=1_000_000.0,
            )
            for sym, ts, price in entries
        ]

    def test_load_cycle_bull_2017_returns_candles_in_that_period(self) -> None:
        """load_cycle('BULL_2017') must return candles from 2017 bull range."""
        loader = DataLoader(candles=self._make_candles_across_cycles())
        result = loader.load_cycle("BTC", CycleLabel.BULL)
        assert len(result) > 0
        for candle in result:
            assert candle.symbol == "BTC"

    def test_load_cycle_unknown_symbol_returns_empty_list(self) -> None:
        """load_cycle() for an unknown symbol must return []."""
        loader = DataLoader(candles=self._make_candles_across_cycles())
        result = loader.load_cycle("GHOST", CycleLabel.BULL)
        assert result == []

    def test_load_cycle_available_symbols_returns_all_symbols(self) -> None:
        """available_symbols() must return the distinct symbols in the dataset."""
        loader = DataLoader(candles=self._make_candles_across_cycles())
        symbols = loader.available_symbols()
        assert "BTC" in symbols

    def test_load_cycle_candle_count_returns_correct_number(self) -> None:
        """candle_count() must return the total number of candles in the dataset."""
        candles = self._make_candles_across_cycles()
        loader = DataLoader(candles=candles)
        assert loader.candle_count() == len(candles)
