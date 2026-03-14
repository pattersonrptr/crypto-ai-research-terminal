"""Tests for app.backtesting.simulation_engine — TDD Red→Green."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.backtesting.data_loader import CycleLabel, DataLoader, HistoricalCandle
from app.backtesting.simulation_engine import (
    SimulationConfig,
    SimulationEngine,
    SimulationResult,
    TradeEvent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_candle(symbol: str, ts: datetime, close: float) -> HistoricalCandle:
    return HistoricalCandle(
        symbol=symbol,
        timestamp=ts,
        open=close * 0.99,
        high=close * 1.02,
        low=close * 0.97,
        close=close,
        volume_usd=1_000_000.0,
    )


def _rising_candles(symbol: str = "BTC", n: int = 10) -> list[HistoricalCandle]:
    """10 candles with a steady 10% rise each day starting 2021-01-01."""
    base = datetime(2021, 1, 1, tzinfo=UTC)
    from datetime import timedelta

    price = 10_000.0
    result = []
    for i in range(n):
        ts = base + timedelta(days=i)
        result.append(_make_candle(symbol, ts, price))
        price *= 1.10
    return result


def _flat_candles(
    symbol: str = "BTC", n: int = 10, price: float = 1_000.0
) -> list[HistoricalCandle]:
    """n candles all at the same price."""
    base = datetime(2021, 1, 1, tzinfo=UTC)
    from datetime import timedelta

    return [_make_candle(symbol, base + timedelta(days=i), price) for i in range(n)]


# ---------------------------------------------------------------------------
# TestSimulationConfig
# ---------------------------------------------------------------------------


class TestSimulationConfig:
    """Unit tests for SimulationConfig validation."""

    def test_simulation_config_default_values_are_valid(self) -> None:
        """Default SimulationConfig must have sensible defaults."""
        cfg = SimulationConfig()
        assert 0.0 < cfg.buy_threshold <= 1.0
        assert 0.0 < cfg.sell_threshold <= 1.0
        assert cfg.initial_capital > 0.0

    def test_simulation_config_custom_values_are_accepted(self) -> None:
        """SimulationConfig must accept custom buy/sell thresholds and capital."""
        cfg = SimulationConfig(buy_threshold=0.7, sell_threshold=0.4, initial_capital=50_000.0)
        assert cfg.buy_threshold == pytest.approx(0.7)
        assert cfg.sell_threshold == pytest.approx(0.4)
        assert cfg.initial_capital == pytest.approx(50_000.0)

    def test_simulation_config_buy_threshold_above_one_raises(self) -> None:
        """buy_threshold > 1.0 must raise ValueError."""
        with pytest.raises(ValueError, match="buy_threshold"):
            SimulationConfig(buy_threshold=1.5)

    def test_simulation_config_sell_threshold_below_zero_raises(self) -> None:
        """sell_threshold < 0.0 must raise ValueError."""
        with pytest.raises(ValueError, match="sell_threshold"):
            SimulationConfig(sell_threshold=-0.1)

    def test_simulation_config_initial_capital_zero_raises(self) -> None:
        """initial_capital <= 0 must raise ValueError."""
        with pytest.raises(ValueError, match="initial_capital"):
            SimulationConfig(initial_capital=0.0)


# ---------------------------------------------------------------------------
# TestTradeEvent
# ---------------------------------------------------------------------------


class TestTradeEvent:
    """Unit tests for the TradeEvent dataclass."""

    def test_trade_event_fields_are_set_correctly(self) -> None:
        """TradeEvent must store symbol, timestamp, action, price and quantity."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        event = TradeEvent(symbol="BTC", timestamp=ts, action="BUY", price=30_000.0, quantity=0.5)
        assert event.symbol == "BTC"
        assert event.action == "BUY"
        assert event.price == pytest.approx(30_000.0)
        assert event.quantity == pytest.approx(0.5)

    def test_trade_event_value_is_price_times_quantity(self) -> None:
        """value property must equal price * quantity."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        event = TradeEvent(symbol="BTC", timestamp=ts, action="BUY", price=30_000.0, quantity=2.0)
        assert event.value == pytest.approx(60_000.0)


# ---------------------------------------------------------------------------
# TestSimulationResult
# ---------------------------------------------------------------------------


class TestSimulationResult:
    """Unit tests for the SimulationResult dataclass."""

    def test_simulation_result_fields_are_set(self) -> None:
        """SimulationResult must expose final_capital, trades, return_pct."""
        result = SimulationResult(
            final_capital=120_000.0,
            initial_capital=100_000.0,
            trades=[],
        )
        assert result.final_capital == pytest.approx(120_000.0)
        assert result.initial_capital == pytest.approx(100_000.0)
        assert result.trades == []

    def test_simulation_result_return_pct_computed_correctly(self) -> None:
        """return_pct must equal (final - initial) / initial * 100."""
        result = SimulationResult(final_capital=110_000.0, initial_capital=100_000.0, trades=[])
        assert result.return_pct == pytest.approx(10.0)

    def test_simulation_result_return_pct_loss(self) -> None:
        """return_pct must be negative when final_capital < initial_capital."""
        result = SimulationResult(final_capital=80_000.0, initial_capital=100_000.0, trades=[])
        assert result.return_pct == pytest.approx(-20.0)

    def test_simulation_result_n_trades_equals_len_of_trades(self) -> None:
        """n_trades must equal len(trades)."""
        ts = datetime(2021, 1, 1, tzinfo=UTC)
        trade = TradeEvent(symbol="BTC", timestamp=ts, action="BUY", price=1.0, quantity=1.0)
        result = SimulationResult(final_capital=100.0, initial_capital=100.0, trades=[trade])
        assert result.n_trades == 1


# ---------------------------------------------------------------------------
# TestSimulationEngine
# ---------------------------------------------------------------------------


class TestSimulationEngineEdgeCases:
    """Edge-case tests for SimulationEngine.run()."""

    def test_run_empty_candles_returns_no_trades(self) -> None:
        """run() with no candles must return 0 trades and unchanged capital."""
        engine = SimulationEngine(SimulationConfig(initial_capital=10_000.0))
        loader = DataLoader(candles=[])
        result = engine.run(loader, "BTC")
        assert result.n_trades == 0
        assert result.final_capital == pytest.approx(10_000.0)

    def test_run_single_candle_returns_no_trades(self) -> None:
        """run() with a single candle cannot generate a complete BUY+SELL cycle."""
        engine = SimulationEngine(SimulationConfig(initial_capital=10_000.0))
        candle = _make_candle("BTC", datetime(2021, 1, 1, tzinfo=UTC), 30_000.0)
        loader = DataLoader(candles=[candle])
        result = engine.run(loader, "BTC")
        assert result.n_trades == 0


class TestSimulationEngineRunning:
    """Functional tests for SimulationEngine.run() with rising/falling prices."""

    def test_run_rising_prices_produces_at_least_one_buy(self) -> None:
        """Steadily rising prices must trigger at least one BUY trade."""
        cfg = SimulationConfig(buy_threshold=0.5, sell_threshold=0.3, initial_capital=100_000.0)
        engine = SimulationEngine(cfg)
        loader = DataLoader(candles=_rising_candles("BTC", n=30))
        result = engine.run(loader, "BTC")
        buys = [t for t in result.trades if t.action == "BUY"]
        assert len(buys) >= 1

    def test_run_flat_prices_produces_no_trades(self) -> None:
        """Flat prices with zero momentum must produce no trades."""
        cfg = SimulationConfig(buy_threshold=0.8, sell_threshold=0.3, initial_capital=10_000.0)
        engine = SimulationEngine(cfg)
        loader = DataLoader(candles=_flat_candles("BTC", n=20))
        result = engine.run(loader, "BTC")
        assert result.n_trades == 0

    def test_run_returns_simulation_result_instance(self) -> None:
        """run() must always return a SimulationResult, even with no data."""
        engine = SimulationEngine(SimulationConfig())
        loader = DataLoader(candles=[])
        result = engine.run(loader, "BTC")
        assert isinstance(result, SimulationResult)

    def test_run_final_capital_is_non_negative(self) -> None:
        """final_capital must never be negative (no leveraged shorts)."""
        cfg = SimulationConfig(initial_capital=10_000.0)
        engine = SimulationEngine(cfg)
        loader = DataLoader(candles=_rising_candles("BTC", n=50))
        result = engine.run(loader, "BTC")
        assert result.final_capital >= 0.0

    def test_run_trade_events_have_correct_symbol(self) -> None:
        """All trade events must reference the queried symbol."""
        cfg = SimulationConfig(buy_threshold=0.5, sell_threshold=0.3, initial_capital=100_000.0)
        engine = SimulationEngine(cfg)
        loader = DataLoader(candles=_rising_candles("ETH", n=30))
        result = engine.run(loader, "ETH")
        for trade in result.trades:
            assert trade.symbol == "ETH"

    def test_run_with_cycle_label_loads_correct_data(self) -> None:
        """run_cycle() must load data for the given CycleLabel and symbol."""
        cfg = SimulationConfig(buy_threshold=0.5, sell_threshold=0.3, initial_capital=50_000.0)
        engine = SimulationEngine(cfg)
        # Build candles in the BULL cycle range
        from datetime import timedelta

        base = datetime(2017, 3, 1, tzinfo=UTC)
        candles = [
            _make_candle("BTC", base + timedelta(days=i), 1_000.0 + i * 100) for i in range(60)
        ]
        loader = DataLoader(candles=candles)
        result = engine.run_cycle(loader, "BTC", CycleLabel.BULL)
        assert isinstance(result, SimulationResult)
