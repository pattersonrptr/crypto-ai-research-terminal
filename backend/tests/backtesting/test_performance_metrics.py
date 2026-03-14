"""Tests for app.backtesting.performance_metrics — TDD Red→Green."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.backtesting.performance_metrics import MetricsReport, PerformanceMetrics
from app.backtesting.simulation_engine import SimulationResult, TradeEvent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts(day: int) -> datetime:
    return datetime(2021, 1, day, tzinfo=UTC)


def _buy(price: float, qty: float = 1.0) -> TradeEvent:
    return TradeEvent(symbol="BTC", timestamp=_ts(1), action="BUY", price=price, quantity=qty)


def _sell(price: float, qty: float = 1.0) -> TradeEvent:
    return TradeEvent(symbol="BTC", timestamp=_ts(2), action="SELL", price=price, quantity=qty)


def _result_with_return(return_pct: float, n_trades: int = 2) -> SimulationResult:
    """Build a SimulationResult with the given return percentage."""
    initial = 10_000.0
    final = initial * (1 + return_pct / 100)
    return SimulationResult(
        final_capital=final,
        initial_capital=initial,
        trades=[_buy(100.0), _sell(100.0 * (1 + return_pct / 100))] if n_trades == 2 else [],
    )


# ---------------------------------------------------------------------------
# TestMetricsReport
# ---------------------------------------------------------------------------


class TestMetricsReport:
    """Unit tests for the MetricsReport dataclass."""

    def test_metrics_report_required_fields_are_set(self) -> None:
        """MetricsReport must store total_return_pct, n_trades, win_rate, sharpe_ratio."""
        report = MetricsReport(
            total_return_pct=25.0,
            n_trades=10,
            win_rate=0.6,
            sharpe_ratio=1.5,
            max_drawdown_pct=15.0,
            avg_trade_return_pct=2.5,
        )
        assert report.total_return_pct == pytest.approx(25.0)
        assert report.n_trades == 10
        assert report.win_rate == pytest.approx(0.6)
        assert report.sharpe_ratio == pytest.approx(1.5)
        assert report.max_drawdown_pct == pytest.approx(15.0)
        assert report.avg_trade_return_pct == pytest.approx(2.5)

    def test_metrics_report_is_profitable_true_when_return_positive(self) -> None:
        """is_profitable must be True when total_return_pct > 0."""
        report = MetricsReport(
            total_return_pct=10.0,
            n_trades=4,
            win_rate=0.75,
            sharpe_ratio=1.0,
            max_drawdown_pct=5.0,
            avg_trade_return_pct=2.5,
        )
        assert report.is_profitable is True

    def test_metrics_report_is_profitable_false_when_return_negative(self) -> None:
        """is_profitable must be False when total_return_pct <= 0."""
        report = MetricsReport(
            total_return_pct=-5.0,
            n_trades=4,
            win_rate=0.25,
            sharpe_ratio=-0.5,
            max_drawdown_pct=20.0,
            avg_trade_return_pct=-1.25,
        )
        assert report.is_profitable is False


# ---------------------------------------------------------------------------
# TestPerformanceMetricsComputeEdgeCases
# ---------------------------------------------------------------------------


class TestPerformanceMetricsEdgeCases:
    """Edge cases for PerformanceMetrics.compute()."""

    def test_compute_no_trades_returns_zero_metrics(self) -> None:
        """compute() with no trades must return 0 for n_trades and 0.0 win_rate."""
        pm = PerformanceMetrics()
        result = SimulationResult(final_capital=10_000.0, initial_capital=10_000.0, trades=[])
        report = pm.compute(result)
        assert report.n_trades == 0
        assert report.win_rate == pytest.approx(0.0)

    def test_compute_no_trades_total_return_zero(self) -> None:
        """compute() with no trades must return 0.0 total_return_pct."""
        pm = PerformanceMetrics()
        result = SimulationResult(final_capital=10_000.0, initial_capital=10_000.0, trades=[])
        report = pm.compute(result)
        assert report.total_return_pct == pytest.approx(0.0)

    def test_compute_returns_metrics_report_instance(self) -> None:
        """compute() must always return a MetricsReport."""
        pm = PerformanceMetrics()
        result = SimulationResult(final_capital=10_000.0, initial_capital=10_000.0, trades=[])
        report = pm.compute(result)
        assert isinstance(report, MetricsReport)


# ---------------------------------------------------------------------------
# TestPerformanceMetricsCompute
# ---------------------------------------------------------------------------


class TestPerformanceMetricsCompute:
    """Functional tests for PerformanceMetrics.compute()."""

    def test_compute_total_return_matches_simulation_result(self) -> None:
        """total_return_pct in report must match SimulationResult.return_pct."""
        pm = PerformanceMetrics()
        sim = _result_with_return(30.0)
        report = pm.compute(sim)
        assert report.total_return_pct == pytest.approx(sim.return_pct, abs=0.01)

    def test_compute_n_trades_matches_simulation_trades(self) -> None:
        """n_trades in report must match the number of completed round-trips."""
        pm = PerformanceMetrics()
        trades = [_buy(100.0), _sell(120.0), _buy(120.0), _sell(140.0)]
        sim = SimulationResult(final_capital=11_600.0, initial_capital=10_000.0, trades=trades)
        report = pm.compute(sim)
        assert report.n_trades == 2  # 2 complete BUY+SELL round-trips

    def test_compute_win_rate_all_winning_trades(self) -> None:
        """win_rate must be 1.0 when all round-trips are profitable."""
        pm = PerformanceMetrics()
        # Both round-trips are wins (sell > buy)
        trades = [_buy(100.0), _sell(120.0), _buy(100.0), _sell(115.0)]
        sim = SimulationResult(final_capital=11_750.0, initial_capital=10_000.0, trades=trades)
        report = pm.compute(sim)
        assert report.win_rate == pytest.approx(1.0)

    def test_compute_win_rate_all_losing_trades(self) -> None:
        """win_rate must be 0.0 when all round-trips are losses."""
        pm = PerformanceMetrics()
        trades = [_buy(100.0), _sell(80.0), _buy(100.0), _sell(90.0)]
        sim = SimulationResult(final_capital=8_500.0, initial_capital=10_000.0, trades=trades)
        report = pm.compute(sim)
        assert report.win_rate == pytest.approx(0.0)

    def test_compute_win_rate_half_winning(self) -> None:
        """win_rate must be 0.5 when exactly half the round-trips are wins."""
        pm = PerformanceMetrics()
        trades = [_buy(100.0), _sell(120.0), _buy(100.0), _sell(90.0)]
        sim = SimulationResult(final_capital=10_500.0, initial_capital=10_000.0, trades=trades)
        report = pm.compute(sim)
        assert report.win_rate == pytest.approx(0.5)

    def test_compute_sharpe_ratio_positive_for_profitable_run(self) -> None:
        """sharpe_ratio must be > 0 for a simulation with net positive returns."""
        pm = PerformanceMetrics()
        # 3 winning round-trips
        trades = [
            _buy(100.0),
            _sell(120.0),
            _buy(120.0),
            _sell(144.0),
            _buy(144.0),
            _sell(172.0),
        ]
        sim = SimulationResult(final_capital=17_200.0, initial_capital=10_000.0, trades=trades)
        report = pm.compute(sim)
        assert report.sharpe_ratio > 0.0

    def test_compute_max_drawdown_non_negative(self) -> None:
        """max_drawdown_pct must always be >= 0."""
        pm = PerformanceMetrics()
        sim = _result_with_return(-20.0)
        report = pm.compute(sim)
        assert report.max_drawdown_pct >= 0.0

    def test_compute_avg_trade_return_pct_zero_when_no_trades(self) -> None:
        """avg_trade_return_pct must be 0.0 when there are no round-trips."""
        pm = PerformanceMetrics()
        sim = SimulationResult(final_capital=10_000.0, initial_capital=10_000.0, trades=[])
        report = pm.compute(sim)
        assert report.avg_trade_return_pct == pytest.approx(0.0)
