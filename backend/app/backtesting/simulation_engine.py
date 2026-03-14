"""Simulation engine — replays the model signal on historical candles.

The engine applies a simple momentum-based buy/sell strategy to a stream of
:class:`HistoricalCandle` objects and produces a :class:`SimulationResult`
with trade events and final portfolio value.

Strategy (configurable via :class:`SimulationConfig`):
- **BUY** when the rolling price momentum score exceeds ``buy_threshold``.
- **SELL** when the momentum score falls below ``sell_threshold``.
- Position sizing: invest the full available cash in a single position at a
  time (no fractional positions, no leverage).

This module is part of the Backtesting Engine (Phase 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from datetime import datetime

    from app.backtesting.data_loader import CycleLabel, DataLoader, HistoricalCandle

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_MOMENTUM_WINDOW: int = 5  # candles used to compute rolling momentum score


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class SimulationConfig:
    """Parameters controlling the simulation strategy.

    Args:
        buy_threshold: Momentum score in (0, 1] above which we BUY. Default 0.6.
        sell_threshold: Momentum score in [0, 1) below which we SELL. Default 0.4.
        initial_capital: Starting cash in USD. Default 10 000.
    """

    buy_threshold: float = 0.6
    sell_threshold: float = 0.4
    initial_capital: float = 10_000.0

    def __post_init__(self) -> None:
        if not 0.0 < self.buy_threshold <= 1.0:
            raise ValueError(f"buy_threshold must be in (0, 1], got {self.buy_threshold}")
        if not 0.0 <= self.sell_threshold < 1.0:
            raise ValueError(f"sell_threshold must be in [0, 1), got {self.sell_threshold}")
        if self.initial_capital <= 0.0:
            raise ValueError(f"initial_capital must be > 0, got {self.initial_capital}")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TradeEvent:
    """A single buy or sell trade executed during the simulation.

    Args:
        symbol: Token ticker.
        timestamp: UTC datetime when the trade was executed.
        action: ``"BUY"`` or ``"SELL"``.
        price: Execution price in USD.
        quantity: Number of tokens traded.
    """

    symbol: str
    timestamp: datetime
    action: str
    price: float
    quantity: float

    @property
    def value(self) -> float:
        """Return the total USD value of this trade (price × quantity)."""
        return self.price * self.quantity


@dataclass
class SimulationResult:
    """Output of a single simulation run.

    Args:
        final_capital: Portfolio value in USD at simulation end.
        initial_capital: Starting capital in USD.
        trades: Ordered list of :class:`TradeEvent` objects.
    """

    final_capital: float
    initial_capital: float
    trades: list[TradeEvent] = field(default_factory=list)

    @property
    def return_pct(self) -> float:
        """Return percentage gain/loss relative to initial capital."""
        return (self.final_capital - self.initial_capital) / self.initial_capital * 100.0

    @property
    def n_trades(self) -> int:
        """Return the total number of executed trades."""
        return len(self.trades)


# ---------------------------------------------------------------------------
# SimulationEngine
# ---------------------------------------------------------------------------


def _momentum_score(candles: list[HistoricalCandle], idx: int, window: int) -> float:
    """Compute a simple momentum score in [0, 1] for the candle at *idx*.

    The score is the fraction of the past *window* candles where the close
    was higher than the previous close.  Returns 0.5 when there is
    insufficient history.
    """
    if idx < window:
        return 0.5
    ups = sum(
        1 for i in range(idx - window + 1, idx + 1) if candles[i].close > candles[i - 1].close
    )
    return ups / window


class SimulationEngine:
    """Replays a momentum-based trading strategy on historical candle data.

    Usage::

        engine = SimulationEngine(SimulationConfig())
        result = engine.run(loader, "BTC")
    """

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self._cfg = config or SimulationConfig()

    def run(self, loader: DataLoader, symbol: str) -> SimulationResult:
        """Run the simulation for *symbol* over all candles in *loader*.

        Args:
            loader: :class:`DataLoader` containing the candle dataset.
            symbol: Token ticker to simulate.

        Returns:
            A :class:`SimulationResult` with trade events and final capital.
        """
        candles = loader.load_symbol(symbol)
        return self._simulate(candles, symbol)

    def run_cycle(
        self,
        loader: DataLoader,
        symbol: str,
        cycle: CycleLabel,
    ) -> SimulationResult:
        """Run the simulation for *symbol* within a pre-defined cycle range.

        Args:
            loader: :class:`DataLoader` containing the candle dataset.
            symbol: Token ticker to simulate.
            cycle: :class:`CycleLabel` defining the date window.

        Returns:
            A :class:`SimulationResult` with trade events and final capital.
        """
        candles = loader.load_cycle(symbol, cycle)
        return self._simulate(candles, symbol)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _simulate(self, candles: list[HistoricalCandle], symbol: str) -> SimulationResult:
        """Core simulation loop over a pre-loaded list of candles."""
        cfg = self._cfg
        cash: float = cfg.initial_capital
        holdings: float = 0.0  # tokens held
        trades: list[TradeEvent] = []

        for idx, candle in enumerate(candles):
            score = _momentum_score(candles, idx, _MOMENTUM_WINDOW)
            price = candle.close

            if holdings == 0.0 and score > cfg.buy_threshold and cash > 0.0:
                # BUY — invest all available cash
                quantity = cash / price
                holdings = quantity
                cash = 0.0
                trades.append(
                    TradeEvent(
                        symbol=symbol,
                        timestamp=candle.timestamp,
                        action="BUY",
                        price=price,
                        quantity=quantity,
                    )
                )
                logger.debug("simulation.buy", symbol=symbol, price=price, qty=quantity)

            elif holdings > 0.0 and score < cfg.sell_threshold:
                # SELL — liquidate full position
                cash = holdings * price
                trades.append(
                    TradeEvent(
                        symbol=symbol,
                        timestamp=candle.timestamp,
                        action="SELL",
                        price=price,
                        quantity=holdings,
                    )
                )
                logger.debug("simulation.sell", symbol=symbol, price=price, qty=holdings)
                holdings = 0.0

        # Liquidate any open position at final candle price
        if holdings > 0.0 and candles:
            final_price = candles[-1].close
            cash = holdings * final_price

        final_capital = max(0.0, cash)
        logger.info(
            "simulation.complete",
            symbol=symbol,
            n_trades=len(trades),
            final_capital=final_capital,
        )
        return SimulationResult(
            final_capital=final_capital,
            initial_capital=cfg.initial_capital,
            trades=trades,
        )
