"""OpportunityEngine — composite opportunity score combining all sub-scores.

Phase 1: only fundamental_score is available.
Phase 2: adds growth_score from dev and social metrics.
Phase 9: full 5-pillar formula with cycle-leader boost.
Phase 10: cycle-aware scoring adjustment (bear → dampen, bull → boost).

.. note:: **Phase 12 tuning reminder**

   Current weights (risk=10%, growth=25%) may under-penalise speculative
   tokens and over-reward volume-driven momentum.  Phase 12 backtesting
   should evaluate alternative weight distributions.  See also the
   ``HeuristicSubScorer`` module docstring for related concerns.
"""

from __future__ import annotations

from app.analysis.cycle_detector import CycleDetector, CyclePhase
from app.exceptions import ScoringError
from app.processors.normalizer import clamp

# Phase 2 weights (must sum to 1.0) — kept for backward compatibility
_WEIGHT_FUNDAMENTAL = 0.60
_WEIGHT_GROWTH = 0.40

# Phase 9 weights (must sum to 1.0)
_W_FUNDAMENTAL = 0.30
_W_GROWTH = 0.25
_W_NARRATIVE = 0.20
_W_LISTING = 0.15
_W_RISK_ADJ = 0.10

# Maximum cycle-leader boost: 10 %
_CYCLE_BOOST_MAX = 0.10


def _validate_score(name: str, value: float) -> None:
    """Raise ScoringError if *value* is not in [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ScoringError(f"OpportunityEngine: {name} must be in [0, 1], got {value}")


class OpportunityEngine:
    """Combines sub-scores into a single composite opportunity score in [0, 1]."""

    @staticmethod
    def composite_score(fundamental_score: float, growth_score: float | None = None) -> float:
        """Return a composite opportunity score in [0, 1].

        Phase 1: when growth_score is None, composite equals fundamental_score.
        Phase 2: composite = 60% fundamental + 40% growth.

        Args:
            fundamental_score: A value in [0, 1] produced by ``FundamentalScorer``.
            growth_score: Optional value in [0, 1] from ``GrowthScorer``.

        Raises:
            ScoringError: If any score is outside [0, 1].
        """
        _validate_score("fundamental_score", fundamental_score)

        if growth_score is None:
            return clamp(fundamental_score, 0.0, 1.0)

        _validate_score("growth_score", growth_score)

        composite = _WEIGHT_FUNDAMENTAL * fundamental_score + _WEIGHT_GROWTH * growth_score
        return clamp(composite, 0.0, 1.0)

    @staticmethod
    def full_composite_score(
        *,
        fundamental: float,
        growth: float,
        narrative: float,
        listing: float,
        risk: float,
        cycle_leader_prob: float = 0.0,
        weights: dict[str, float] | None = None,
    ) -> float:
        """Return the full 5-pillar composite opportunity score in [0, 1].

        Formula (SCOPE.md §9):
            base = w_f×fundamental + w_g×growth + w_n×narrative
                   + w_l×listing + w_r×risk
            composite = base × (1 + cycle_leader_prob × CYCLE_BOOST_MAX)
            clamped to [0, 1]

        Args:
            fundamental: Fundamental sub-score in [0, 1].
            growth: Growth/momentum sub-score in [0, 1].
            narrative: Narrative/trend sub-score in [0, 1].
            listing: Listing probability in [0, 1].
            risk: Risk-adjusted score in [0, 1] (higher = safer).
            cycle_leader_prob: ML cycle-leader probability in [0, 1].
                Defaults to 0.0 (no boost).
            weights: Optional dict with keys ``fundamental``, ``growth``,
                ``narrative``, ``listing``, ``risk``. When ``None``,
                hardcoded Phase 9 defaults are used.

        Raises:
            ScoringError: If any input is outside [0, 1].
        """
        _validate_score("fundamental", fundamental)
        _validate_score("growth", growth)
        _validate_score("narrative", narrative)
        _validate_score("listing", listing)
        _validate_score("risk", risk)
        _validate_score("cycle_leader_prob", cycle_leader_prob)

        w_f = weights["fundamental"] if weights else _W_FUNDAMENTAL
        w_g = weights["growth"] if weights else _W_GROWTH
        w_n = weights["narrative"] if weights else _W_NARRATIVE
        w_l = weights["listing"] if weights else _W_LISTING
        w_r = weights["risk"] if weights else _W_RISK_ADJ

        base = w_f * fundamental + w_g * growth + w_n * narrative + w_l * listing + w_r * risk

        boost = 1.0 + cycle_leader_prob * _CYCLE_BOOST_MAX
        return clamp(base * boost, 0.0, 1.0)

    @staticmethod
    def cycle_adjusted_score(
        base_score: float,
        cycle_phase: CyclePhase | None,
    ) -> float:
        """Apply cycle-phase multiplier to a base opportunity score.

        Phase 10: adjusts scoring based on the detected market cycle:
        - BULL: +10% boost (momentum-friendly environment)
        - ACCUMULATION: neutral (1.0×)
        - DISTRIBUTION: −10% dampen (risk of reversal)
        - BEAR: −25% dampen (preservation mode)

        Args:
            base_score: Opportunity score in [0, 1].
            cycle_phase: Current market cycle phase, or ``None`` if
                cycle detection is unavailable.

        Returns:
            Adjusted score in [0, 1].
        """
        if cycle_phase is None:
            return base_score

        multiplier = CycleDetector.cycle_score_adjustment(cycle_phase)
        return clamp(base_score * multiplier, 0.0, 1.0)
