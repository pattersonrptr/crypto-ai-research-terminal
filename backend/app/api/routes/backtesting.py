"""Backtesting route handlers.

Provides endpoints for the Backtesting Engine (Phase 7 + Phase 12 + Phase 14):
- POST /backtesting/run       — Run a simulation for a symbol over a market cycle
- POST /backtesting/validate  — Run validation metrics on historical data
- POST /backtesting/calibrate — Run weight calibration sweep
- GET  /backtesting/cycles    — List available market cycles
- GET  /backtesting/weights   — Get current active scoring weights
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from enum import Enum

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backtesting.cycle_config import get_cycle, get_cycle_names
from app.backtesting.data_loader import CycleLabel, DataLoader, HistoricalCandle
from app.backtesting.performance_metrics import MetricsReport, PerformanceMetrics
from app.backtesting.simulation_engine import SimulationConfig, SimulationEngine
from app.backtesting.validation_metrics import (
    TokenOutcome,
    generate_validation_report,
)
from app.backtesting.weight_calibrator import calibrate_weights

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


# ---------------------------------------------------------------------------
# Phase 12 — Validation sample data
# ---------------------------------------------------------------------------

# Simulated historical outcomes: model scores (from scoring a Jan 2020 snapshot)
# vs actual multipliers during the 2020-2021 bull cycle.
# This will be replaced with real DB data once historical_snapshots is seeded.

_SAMPLE_OUTCOMES: list[TokenOutcome] = [
    TokenOutcome(symbol="SOL", model_rank=1, model_score=0.88, actual_multiplier=320.0),
    TokenOutcome(symbol="AVAX", model_rank=2, model_score=0.85, actual_multiplier=55.0),
    TokenOutcome(symbol="MATIC", model_rank=3, model_score=0.82, actual_multiplier=95.0),
    TokenOutcome(symbol="LINK", model_rank=4, model_score=0.78, actual_multiplier=12.0),
    TokenOutcome(symbol="UNI", model_rank=5, model_score=0.75, actual_multiplier=18.0),
    TokenOutcome(symbol="AAVE", model_rank=6, model_score=0.72, actual_multiplier=22.0),
    TokenOutcome(symbol="DOT", model_rank=7, model_score=0.70, actual_multiplier=8.5),
    TokenOutcome(symbol="ATOM", model_rank=8, model_score=0.68, actual_multiplier=6.0),
    TokenOutcome(symbol="ETH", model_rank=9, model_score=0.65, actual_multiplier=15.0),
    TokenOutcome(symbol="BTC", model_rank=10, model_score=0.62, actual_multiplier=7.0),
    TokenOutcome(symbol="BNB", model_rank=11, model_score=0.58, actual_multiplier=13.0),
    TokenOutcome(symbol="ADA", model_rank=12, model_score=0.55, actual_multiplier=45.0),
    TokenOutcome(symbol="FTM", model_rank=13, model_score=0.52, actual_multiplier=180.0),
    TokenOutcome(symbol="NEAR", model_rank=14, model_score=0.48, actual_multiplier=35.0),
    TokenOutcome(symbol="ARB", model_rank=15, model_score=0.45, actual_multiplier=2.0),
]


# ---------------------------------------------------------------------------
# Phase 12 — Pydantic schemas for validation endpoints
# ---------------------------------------------------------------------------


class ValidateRequest(BaseModel):
    """Request body for POST /backtesting/validate."""

    k: int = Field(default=10, ge=1, le=100, description="Top-K tokens for metrics")
    winner_threshold: float = Field(
        default=5.0, ge=1.0, description="Multiplier threshold for 'winner'"
    )
    market_multiplier: float = Field(default=2.0, ge=1.0, description="Market benchmark multiplier")


class TokenBreakdownItem(BaseModel):
    """A single token in the validation breakdown."""

    symbol: str
    model_rank: int
    model_score: float
    actual_multiplier: float
    is_winner: bool


class ValidateResponse(BaseModel):
    """Response body for POST /backtesting/validate."""

    precision_at_k: float = Field(ge=0.0, le=1.0)
    recall_at_k: float = Field(ge=0.0, le=1.0)
    hit_rate: float = Field(ge=0.0, le=1.0)
    k: int
    winner_threshold: float
    n_total_tokens: int
    n_winners: int
    model_is_useful: bool
    token_breakdown: list[TokenBreakdownItem]


class CalibrateRequest(BaseModel):
    """Request body for POST /backtesting/calibrate."""

    step: float = Field(default=0.25, ge=0.05, le=0.50, description="Grid step size")
    k: int = Field(default=10, ge=1, le=100, description="Top-K for precision")


class WeightSetResponse(BaseModel):
    """A set of pillar weights."""

    fundamental: float
    growth: float
    narrative: float
    listing: float
    risk: float


class CalibrateResponse(BaseModel):
    """Response body for POST /backtesting/calibrate."""

    best_weights: WeightSetResponse
    best_precision_at_k: float
    n_combinations_tested: int
    improved: bool


# ---------------------------------------------------------------------------
# Phase 12 — Route handlers
# ---------------------------------------------------------------------------


@router.post("/validate", response_model=ValidateResponse)
async def validate_model(request: ValidateRequest) -> ValidateResponse:
    """Run validation metrics on the model's historical predictions.

    Uses sample outcomes (Phase 12). Will be wired to real DB data
    once ``historical_snapshots`` is seeded.

    Args:
        request: Validation parameters (k, thresholds).

    Returns:
        A :class:`ValidateResponse` with precision, recall, hit rate.
    """
    report = generate_validation_report(
        outcomes=_SAMPLE_OUTCOMES,
        k=request.k,
        winner_threshold=request.winner_threshold,
        market_multiplier=request.market_multiplier,
    )

    breakdown = [
        TokenBreakdownItem(
            symbol=o.symbol,
            model_rank=o.model_rank,
            model_score=o.model_score,
            actual_multiplier=o.actual_multiplier,
            is_winner=o.is_winner(threshold=request.winner_threshold),
        )
        for o in report.token_breakdown
    ]

    logger.info(
        "backtesting.validate",
        k=request.k,
        precision=report.precision_at_k,
        recall=report.recall_at_k,
    )

    return ValidateResponse(
        precision_at_k=report.precision_at_k,
        recall_at_k=report.recall_at_k,
        hit_rate=report.hit_rate,
        k=report.k,
        winner_threshold=report.winner_threshold,
        n_total_tokens=report.n_total_tokens,
        n_winners=report.n_winners,
        model_is_useful=report.model_is_useful,
        token_breakdown=breakdown,
    )


@router.post("/calibrate", response_model=CalibrateResponse)
async def calibrate_model_weights(request: CalibrateRequest) -> CalibrateResponse:
    """Run weight calibration sweep on historical validation data.

    Performs a grid search over pillar weights to find the combination
    that maximises Precision@K.

    Args:
        request: Calibration parameters (step size, k).

    Returns:
        A :class:`CalibrateResponse` with best weights and precision.
    """
    result = calibrate_weights(
        outcomes=_SAMPLE_OUTCOMES,
        k=request.k,
        step=request.step,
    )

    logger.info(
        "backtesting.calibrate",
        n_combinations=result.n_combinations_tested,
        best_precision=result.best_precision_at_k,
    )

    return CalibrateResponse(
        best_weights=WeightSetResponse(
            fundamental=result.best_weights.fundamental,
            growth=result.best_weights.growth,
            narrative=result.best_weights.narrative,
            listing=result.best_weights.listing,
            risk=result.best_weights.risk,
        ),
        best_precision_at_k=result.best_precision_at_k,
        n_combinations_tested=result.n_combinations_tested,
        improved=result.improved(baseline_precision=0.5),
    )


# ---------------------------------------------------------------------------
# Phase 14 — Pydantic schemas
# ---------------------------------------------------------------------------


class CycleInfoResponse(BaseModel):
    """Summary info for one market cycle."""

    name: str
    bottom_date: str
    top_date: str
    n_tokens: int


class ActiveWeightsResponse(BaseModel):
    """Currently active scoring weights."""

    fundamental: float
    growth: float
    narrative: float
    listing: float
    risk: float
    source: str


# ---------------------------------------------------------------------------
# Phase 14 — Route handlers
# ---------------------------------------------------------------------------

# Default Phase 9 weights — used when no calibrated weights exist.
_DEFAULT_PHASE9_WEIGHTS = {
    "fundamental": 0.30,
    "growth": 0.25,
    "narrative": 0.20,
    "listing": 0.15,
    "risk": 0.10,
}


@router.get("/cycles", response_model=list[CycleInfoResponse])
async def list_cycles() -> list[CycleInfoResponse]:
    """List all available market cycles for backtesting.

    Returns:
        A list of :class:`CycleInfoResponse` with cycle metadata.
    """
    result: list[CycleInfoResponse] = []
    for name in get_cycle_names():
        cycle = get_cycle(name)
        result.append(
            CycleInfoResponse(
                name=cycle.name,
                bottom_date=cycle.bottom_date.isoformat(),
                top_date=cycle.top_date.isoformat(),
                n_tokens=len(cycle.tokens),
            )
        )
    logger.info("backtesting.list_cycles", n_cycles=len(result))
    return result


@router.get("/weights", response_model=ActiveWeightsResponse)
async def get_active_weights() -> ActiveWeightsResponse:
    """Get the currently active scoring weights.

    Returns the Phase 9 defaults if no calibrated weights have been
    applied yet.

    Returns:
        An :class:`ActiveWeightsResponse`.
    """
    # Phase 14: for now return defaults.  When a calibration is applied
    # and persisted to the DB, this route will read from scoring_weights.
    return ActiveWeightsResponse(
        **_DEFAULT_PHASE9_WEIGHTS,
        source="default_phase9",
    )
