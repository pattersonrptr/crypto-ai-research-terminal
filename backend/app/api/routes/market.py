"""Market route handlers — cycle detection and market-wide metrics.

Phase 10: exposes current market cycle phase derived from
Fear & Greed index, BTC dominance, and total market cap trend.

Endpoints:
- GET /market/cycle — current market cycle phase + confidence + indicators
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.analysis.cycle_data_collector import CycleDataCollector
from app.analysis.cycle_detector import CycleDetector, CyclePhase, CycleResult

router = APIRouter()
logger = structlog.get_logger(__name__)

# Phase descriptions for each cycle phase
_PHASE_DESCRIPTIONS: dict[CyclePhase, str] = {
    CyclePhase.ACCUMULATION: (
        "Market is in accumulation phase. Smart money is building positions "
        "while sentiment is still fearful. Good risk/reward for research."
    ),
    CyclePhase.BULL: (
        "Market is in a bull phase. Rising prices, falling BTC dominance, "
        "and strong greed signal an altcoin-friendly environment."
    ),
    CyclePhase.DISTRIBUTION: (
        "Market is in distribution phase. Greed is elevated but BTC dominance "
        "is rising — large holders may be taking profits. Exercise caution."
    ),
    CyclePhase.BEAR: (
        "Market is in a bear phase. Fear dominates, prices are below long-term "
        "averages. Focus on fundamentals and avoid chasing momentum."
    ),
}


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------


class CycleIndicatorsResponse(BaseModel):
    """Serialised market cycle indicators."""

    btc_dominance: float
    btc_dominance_30d_ago: float
    total_market_cap_usd: float
    total_market_cap_200d_ma: float | None = None
    fear_greed_index: int = Field(ge=0, le=100)
    fear_greed_label: str
    btc_dominance_rising: bool
    market_above_200d_ma: bool | None = None


class CycleResponse(BaseModel):
    """Market cycle detection result."""

    phase: str
    confidence: float = Field(ge=0.0, le=1.0)
    phase_description: str
    indicators: CycleIndicatorsResponse


# ---------------------------------------------------------------------------
# Internal helper (patchable in tests)
# ---------------------------------------------------------------------------


async def _get_cycle_result() -> CycleResult:
    """Fetch live data, classify cycle, and return result.

    This function is separated so tests can patch it to avoid real API calls.
    """
    collector = CycleDataCollector()
    # TODO(Phase 12): load btc_dominance_30d_ago from DB historical snapshots
    # For now, use same as current (conservative — no trend signal)
    indicators = await collector.collect_indicators(btc_dominance_30d_ago=50.0)
    return CycleDetector.classify(indicators)


# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------


@router.get("/cycle", response_model=CycleResponse)
async def get_market_cycle() -> CycleResponse:
    """Return the current market cycle phase with confidence and indicators.

    Uses Fear & Greed index, BTC dominance, and total market cap to
    classify the cycle as accumulation / bull / distribution / bear.
    """
    result = await _get_cycle_result()
    ind = result.indicators

    logger.info(
        "market.cycle.detected",
        phase=result.phase.value,
        confidence=result.confidence,
    )

    return CycleResponse(
        phase=result.phase.value,
        confidence=result.confidence,
        phase_description=_PHASE_DESCRIPTIONS[result.phase],
        indicators=CycleIndicatorsResponse(
            btc_dominance=ind.btc_dominance,
            btc_dominance_30d_ago=ind.btc_dominance_30d_ago,
            total_market_cap_usd=ind.total_market_cap_usd,
            total_market_cap_200d_ma=ind.total_market_cap_200d_ma,
            fear_greed_index=ind.fear_greed_index,
            fear_greed_label=ind.fear_greed_label,
            btc_dominance_rising=ind.btc_dominance_rising,
            market_above_200d_ma=ind.market_above_200d_ma,
        ),
    )
