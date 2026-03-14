"""Backtesting route handlers.

Provides endpoints for the Backtesting Engine (Phase 7):
- POST /backtesting/run  — Run a simulation for a symbol over a market cycle
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from enum import Enum

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backtesting.data_loader import CycleLabel, DataLoader, HistoricalCandle
from app.backtesting.performance_metrics import MetricsReport, PerformanceMetrics
from app.backtesting.simulation_engine import SimulationConfig, SimulationEngine

router = APIRouter()
logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Seed candles — synthetic dataset so the endpoint is runnable without a DB.
# Phase 8 will replace this with a real DB query via DataLoader(candles=...).
# ---------------------------------------------------------------------------

_BASE_PRICES: dict[str, float] = {
    "BTC": 1_000.0,
    "ETH": 10.0,
    "SOL": 0.5,
    "BNB": 2.0,
    "AVAX": 1.0,
}

_CYCLE_STARTS: dict[str, datetime] = {
    "bull": datetime(2017, 1, 1, tzinfo=UTC),
    "bear": datetime(2018, 2, 1, tzinfo=UTC),
    "accumulation": datetime(2020, 4, 1, tzinfo=UTC),
}

_CYCLE_DAYS: dict[str, int] = {
    "bull": 395,
    "bear": 760,
    "accumulation": 609,
}


def _generate_seed_candles() -> list[HistoricalCandle]:
    """Generate synthetic OHLCV candles for all known symbols × all cycles."""
    candles: list[HistoricalCandle] = []
    for symbol, base_price in _BASE_PRICES.items():
        for cycle_label, start_dt in _CYCLE_STARTS.items():
            price = base_price
            for day in range(_CYCLE_DAYS[cycle_label]):
                ts = start_dt + timedelta(days=day)
                drift = 1.0 + 0.01 * math.sin(day / 10.0)
                price = max(price * drift, 0.01)
                candles.append(
                    HistoricalCandle(
                        symbol=symbol,
                        timestamp=ts,
                        open=price * 0.99,
                        high=price * 1.01,
                        low=price * 0.98,
                        close=price,
                        volume_usd=price * 1_000_000,
                    )
                )
    return candles


_SEED_CANDLES: list[HistoricalCandle] = _generate_seed_candles()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CycleLabelEnum(str, Enum):
    """Valid market cycle labels."""

    BULL = "bull"
    BEAR = "bear"
    ACCUMULATION = "accumulation"


class BacktestRequest(BaseModel):
    """Request body for POST /backtesting/run."""

    symbol: str = Field(min_length=1, max_length=20, description="Token ticker, e.g. BTC")
    cycle: CycleLabelEnum = Field(
        description="Market cycle to simulate (bull | bear | accumulation)"
    )


class BacktestResponse(BaseModel):
    """Full backtesting result returned to the caller."""

    symbol: str
    cycle: str
    total_return_pct: float
    n_trades: int = Field(ge=0)
    win_rate: float = Field(ge=0.0, le=1.0)
    sharpe_ratio: float
    max_drawdown_pct: float = Field(ge=0.0)
    avg_trade_return_pct: float
    is_profitable: bool


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """Run a backtesting simulation for *symbol* over the specified *cycle*.

    Uses synthetic seed candle data in Phase 7.  Phase 8 will wire this to
    real historical data from the ``historical_candles`` table.

    Args:
        request: Symbol and cycle selection.

    Returns:
        A :class:`BacktestResponse` with full performance metrics.
    """
    loader = DataLoader(candles=_SEED_CANDLES)
    engine = SimulationEngine(SimulationConfig())
    cycle_label = CycleLabel(request.cycle.value)
    result = engine.run_cycle(loader, request.symbol.upper(), cycle_label)

    metrics: MetricsReport = PerformanceMetrics().compute(result)

    logger.info(
        "backtesting.run",
        symbol=request.symbol,
        cycle=request.cycle.value,
        n_trades=metrics.n_trades,
        total_return_pct=metrics.total_return_pct,
    )

    return BacktestResponse(
        symbol=request.symbol.upper(),
        cycle=request.cycle.value,
        total_return_pct=metrics.total_return_pct,
        n_trades=metrics.n_trades,
        win_rate=metrics.win_rate,
        sharpe_ratio=metrics.sharpe_ratio,
        max_drawdown_pct=metrics.max_drawdown_pct,
        avg_trade_return_pct=metrics.avg_trade_return_pct,
        is_profitable=metrics.is_profitable,
    )
