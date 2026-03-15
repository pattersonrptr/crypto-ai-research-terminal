"""CycleDetector — market cycle phase classification.

Uses a combination of on-chain and sentiment indicators to determine
the current cryptocurrency market cycle phase:

- **Accumulation**: Fear zone, market near/below 200d MA, BTC dominance rising
- **Bull**: Greed zone, market above 200d MA, BTC dominance falling (altseason)
- **Distribution**: Greed zone but BTC dominance rising, market near 200d MA
- **Bear**: Extreme fear, market below 200d MA

The classification is rule-based with a weighted-vote scoring system.
Each indicator casts a vote towards one or more phases, and the phase
with the highest vote wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class CyclePhase(str, Enum):
    """Market cycle phases."""

    ACCUMULATION = "accumulation"
    BULL = "bull"
    DISTRIBUTION = "distribution"
    BEAR = "bear"


@dataclass
class CycleIndicators:
    """Raw market indicators used for cycle phase classification.

    Args:
        btc_dominance: Current BTC dominance percentage (e.g. 55.2).
        btc_dominance_30d_ago: BTC dominance 30 days ago.
        total_market_cap_usd: Current total crypto market cap in USD.
        total_market_cap_200d_ma: 200-day moving average of total market cap.
            ``None`` when unavailable.
        fear_greed_index: Fear & Greed index value (0-100).
        fear_greed_label: Human-readable label (e.g. "greed", "extreme fear").
    """

    btc_dominance: float
    btc_dominance_30d_ago: float
    total_market_cap_usd: float
    fear_greed_index: int
    fear_greed_label: str
    total_market_cap_200d_ma: float | None = None

    @property
    def btc_dominance_rising(self) -> bool:
        """Return ``True`` if BTC dominance is higher than 30 days ago."""
        return self.btc_dominance > self.btc_dominance_30d_ago

    @property
    def market_above_200d_ma(self) -> bool | None:
        """Return ``True``/``False`` relative to 200d MA, or ``None`` if unavailable."""
        if self.total_market_cap_200d_ma is None:
            return None
        return self.total_market_cap_usd > self.total_market_cap_200d_ma

    def to_dict(self) -> dict[str, Any]:
        """Serialise indicators to a plain dict."""
        return {
            "btc_dominance": self.btc_dominance,
            "btc_dominance_30d_ago": self.btc_dominance_30d_ago,
            "total_market_cap_usd": self.total_market_cap_usd,
            "total_market_cap_200d_ma": self.total_market_cap_200d_ma,
            "fear_greed_index": self.fear_greed_index,
            "fear_greed_label": self.fear_greed_label,
            "btc_dominance_rising": self.btc_dominance_rising,
            "market_above_200d_ma": self.market_above_200d_ma,
        }


@dataclass
class CycleResult:
    """Result from cycle phase classification.

    Args:
        phase: Detected market cycle phase.
        confidence: Confidence score in [0, 1].
        indicators: The raw indicators used for classification.
    """

    phase: CyclePhase
    confidence: float
    indicators: CycleIndicators

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for API responses."""
        return {
            "phase": self.phase.value,
            "confidence": round(self.confidence, 2),
            "indicators": self.indicators.to_dict(),
        }


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Fear & Greed zones
_FG_EXTREME_FEAR = 20
_FG_FEAR = 40
_FG_GREED = 60
_FG_EXTREME_GREED = 75

# Market cap vs 200d MA tolerance (±5% is "near")
_MA_NEAR_TOLERANCE = 0.05

# Cycle score adjustments for OpportunityEngine
_CYCLE_ADJUSTMENTS: dict[CyclePhase, float] = {
    CyclePhase.ACCUMULATION: 1.0,  # neutral — good time to build positions
    CyclePhase.BULL: 1.10,  # 10% boost for momentum tokens
    CyclePhase.DISTRIBUTION: 0.90,  # 10% dampen — risk of reversal
    CyclePhase.BEAR: 0.75,  # 25% dampen — preservation mode
}


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class CycleDetector:
    """Classifies the current market cycle phase from on-chain + sentiment data.

    The algorithm uses a *weighted-vote* approach:
    1. Fear & Greed index → strongest signal
    2. Market cap vs 200d MA → trend confirmation
    3. BTC dominance direction → altseason / risk-off signal

    Each indicator adds votes to candidate phases.  The phase with the
    most votes wins.  Confidence = winning votes / total possible votes.
    """

    @staticmethod
    def classify(indicators: CycleIndicators) -> CycleResult:
        """Classify market cycle phase from the given indicators.

        Args:
            indicators: Populated :class:`CycleIndicators`.

        Returns:
            :class:`CycleResult` with the detected phase and confidence.
        """
        votes: dict[CyclePhase, float] = {phase: 0.0 for phase in CyclePhase}

        # Track how many vote-points are possible (for confidence calc)
        total_weight = 0.0

        # ----- Signal 1: Fear & Greed index (weight 3) ----- #
        fg = indicators.fear_greed_index
        weight_fg = 3.0
        total_weight += weight_fg

        if fg <= _FG_EXTREME_FEAR:
            votes[CyclePhase.BEAR] += weight_fg
        elif fg <= _FG_FEAR:
            votes[CyclePhase.ACCUMULATION] += weight_fg * 0.7
            votes[CyclePhase.BEAR] += weight_fg * 0.3
        elif fg <= _FG_GREED:
            # Neutral — small vote towards accumulation
            votes[CyclePhase.ACCUMULATION] += weight_fg * 0.5
            votes[CyclePhase.DISTRIBUTION] += weight_fg * 0.3
            votes[CyclePhase.BULL] += weight_fg * 0.2
        elif fg <= _FG_EXTREME_GREED:
            votes[CyclePhase.BULL] += weight_fg * 0.5
            votes[CyclePhase.DISTRIBUTION] += weight_fg * 0.5
        else:
            votes[CyclePhase.BULL] += weight_fg * 0.8
            votes[CyclePhase.DISTRIBUTION] += weight_fg * 0.2

        # ----- Signal 2: Market cap vs 200d MA (weight 2) ----- #
        above_ma = indicators.market_above_200d_ma
        if above_ma is not None:
            weight_ma = 2.0
            total_weight += weight_ma

            # Calculate how far above/below the MA we are
            assert indicators.total_market_cap_200d_ma is not None  # guarded by above_ma
            ratio = indicators.total_market_cap_usd / indicators.total_market_cap_200d_ma

            if ratio > 1.0 + _MA_NEAR_TOLERANCE:
                # Clearly above → bullish
                votes[CyclePhase.BULL] += weight_ma * 0.7
                votes[CyclePhase.DISTRIBUTION] += weight_ma * 0.3
            elif ratio < 1.0 - _MA_NEAR_TOLERANCE:
                # Clearly below → bearish
                votes[CyclePhase.BEAR] += weight_ma * 0.6
                votes[CyclePhase.ACCUMULATION] += weight_ma * 0.4
            else:
                # Near the MA — transitional
                votes[CyclePhase.ACCUMULATION] += weight_ma * 0.4
                votes[CyclePhase.DISTRIBUTION] += weight_ma * 0.4
                votes[CyclePhase.BULL] += weight_ma * 0.1
                votes[CyclePhase.BEAR] += weight_ma * 0.1

        # ----- Signal 3: BTC dominance trend (weight 1.5) ----- #
        weight_dom = 1.5
        total_weight += weight_dom

        if indicators.btc_dominance_rising:
            # Rising BTC dom = risk-off, capital flows to BTC
            votes[CyclePhase.ACCUMULATION] += weight_dom * 0.3
            votes[CyclePhase.DISTRIBUTION] += weight_dom * 0.4
            votes[CyclePhase.BEAR] += weight_dom * 0.3
        else:
            # Falling BTC dom = altseason, risk-on
            votes[CyclePhase.BULL] += weight_dom * 0.7
            votes[CyclePhase.ACCUMULATION] += weight_dom * 0.3

        # ----- Determine winner ----- #
        winning_phase = max(votes, key=lambda p: votes[p])
        winning_votes = votes[winning_phase]
        confidence = winning_votes / total_weight if total_weight > 0 else 0.0
        confidence = min(max(confidence, 0.0), 1.0)

        logger.info(
            "cycle.classify",
            phase=winning_phase.value,
            confidence=round(confidence, 2),
            votes={p.value: round(v, 2) for p, v in votes.items()},
            fg=fg,
            btc_dom_rising=indicators.btc_dominance_rising,
            above_200d_ma=above_ma,
        )

        return CycleResult(
            phase=winning_phase,
            confidence=round(confidence, 2),
            indicators=indicators,
        )

    @staticmethod
    def cycle_score_adjustment(phase: CyclePhase) -> float:
        """Return a multiplier for the OpportunityEngine based on cycle phase.

        - BULL: 1.10 (10% boost)
        - ACCUMULATION: 1.0 (neutral)
        - DISTRIBUTION: 0.90 (10% dampen)
        - BEAR: 0.75 (25% dampen)

        Args:
            phase: The current market cycle phase.

        Returns:
            Multiplier in (0, 1.5].
        """
        return _CYCLE_ADJUSTMENTS[phase]
