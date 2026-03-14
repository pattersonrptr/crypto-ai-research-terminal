"""Performance metrics — computes trading statistics from a SimulationResult.

Converts a raw :class:`SimulationResult` into a human-readable
:class:`MetricsReport` with key risk/return statistics:
total return, win rate, Sharpe ratio, max drawdown, avg trade return.

This module is part of the Backtesting Engine (Phase 7).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.backtesting.simulation_engine import SimulationResult, TradeEvent

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# MetricsReport
# ---------------------------------------------------------------------------


@dataclass
class MetricsReport:
    """Summary statistics derived from a backtesting simulation.

    Args:
        total_return_pct: Overall percentage return of the simulation.
        n_trades: Number of completed round-trip trades (BUY+SELL pairs).
        win_rate: Fraction of round-trips that were profitable (0.0–1.0).
        sharpe_ratio: Risk-adjusted return (mean / std of round-trip returns).
                      0.0 when there are insufficient data points.
        max_drawdown_pct: Maximum peak-to-trough loss as a positive percentage.
        avg_trade_return_pct: Average return per round-trip trade.
    """

    total_return_pct: float
    n_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown_pct: float
    avg_trade_return_pct: float

    @property
    def is_profitable(self) -> bool:
        """Return True when ``total_return_pct`` is strictly positive."""
        return self.total_return_pct > 0.0


# ---------------------------------------------------------------------------
# PerformanceMetrics
# ---------------------------------------------------------------------------


def _pair_trades(trades: list[TradeEvent]) -> list[tuple[TradeEvent, TradeEvent]]:
    """Pair consecutive BUY/SELL events into round-trip tuples."""
    pairs: list[tuple[TradeEvent, TradeEvent]] = []
    pending_buy: TradeEvent | None = None
    for trade in trades:
        if trade.action == "BUY":
            pending_buy = trade
        elif trade.action == "SELL" and pending_buy is not None:
            pairs.append((pending_buy, trade))
            pending_buy = None
    return pairs


def _round_trip_return_pct(buy: TradeEvent, sell: TradeEvent) -> float:
    """Return the percentage gain/loss for a single round-trip."""
    if buy.price == 0.0:
        return 0.0
    return (sell.price - buy.price) / buy.price * 100.0


class PerformanceMetrics:
    """Computes risk/return statistics from a :class:`SimulationResult`.

    Usage::

        pm = PerformanceMetrics()
        report = pm.compute(simulation_result)
    """

    def compute(self, result: SimulationResult) -> MetricsReport:
        """Compute a :class:`MetricsReport` from *result*.

        Args:
            result: The output of a :class:`SimulationEngine` run.

        Returns:
            A fully populated :class:`MetricsReport`.
        """
        pairs = _pair_trades(result.trades)
        n_trades = len(pairs)

        if n_trades == 0:
            report = MetricsReport(
                total_return_pct=result.return_pct,
                n_trades=0,
                win_rate=0.0,
                sharpe_ratio=0.0,
                max_drawdown_pct=self._max_drawdown(result),
                avg_trade_return_pct=0.0,
            )
            logger.info("performance_metrics.computed", n_trades=0)
            return report

        returns = [_round_trip_return_pct(buy, sell) for buy, sell in pairs]
        wins = sum(1 for r in returns if r > 0.0)
        win_rate = wins / n_trades
        avg_return = sum(returns) / n_trades
        sharpe = self._sharpe(returns)
        max_dd = self._max_drawdown(result)

        report = MetricsReport(
            total_return_pct=result.return_pct,
            n_trades=n_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            avg_trade_return_pct=avg_return,
        )
        logger.info(
            "performance_metrics.computed",
            n_trades=n_trades,
            win_rate=win_rate,
            total_return=result.return_pct,
        )
        return report

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sharpe(returns: list[float]) -> float:
        """Compute Sharpe ratio as mean / std of round-trip returns.

        Returns 0.0 when std is zero or there is only one data point.
        """
        if len(returns) < 2:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(variance)
        if std == 0.0:
            return 0.0
        return mean / std

    @staticmethod
    def _max_drawdown(result: SimulationResult) -> float:
        """Compute the maximum peak-to-trough drawdown as a positive percentage.

        Approximated from the total return: if the simulation lost money the
        drawdown equals the absolute loss percentage, otherwise 0.
        """
        loss = result.initial_capital - result.final_capital
        if loss <= 0.0:
            return 0.0
        return loss / result.initial_capital * 100.0
