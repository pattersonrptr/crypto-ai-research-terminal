"""OpportunityEngine — composite opportunity score combining all sub-scores.

Phase 1: only fundamental_score is available.
Phase 2: adds growth_score from dev and social metrics.
Phase 9: full 5-pillar formula with cycle-leader boost.

.. note:: **Phase 12 tuning reminder**

   Current weights (risk=10%, growth=25%) may under-penalise speculative
   tokens and over-reward volume-driven momentum.  Phase 12 backtesting
   should evaluate alternative weight distributions.  See also the
   ``HeuristicSubScorer`` module docstring for related concerns.
"""

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
    ) -> float:
        """Return the full 5-pillar composite opportunity score in [0, 1].

        Formula (SCOPE.md §9):
            base = 0.30×fundamental + 0.25×growth + 0.20×narrative
                   + 0.15×listing + 0.10×risk
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

        Raises:
            ScoringError: If any input is outside [0, 1].
        """
        _validate_score("fundamental", fundamental)
        _validate_score("growth", growth)
        _validate_score("narrative", narrative)
        _validate_score("listing", listing)
        _validate_score("risk", risk)
        _validate_score("cycle_leader_prob", cycle_leader_prob)

        base = (
            _W_FUNDAMENTAL * fundamental
            + _W_GROWTH * growth
            + _W_NARRATIVE * narrative
            + _W_LISTING * listing
            + _W_RISK_ADJ * risk
        )

        boost = 1.0 + cycle_leader_prob * _CYCLE_BOOST_MAX
        return clamp(base * boost, 0.0, 1.0)
