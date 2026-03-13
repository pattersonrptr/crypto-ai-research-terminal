"""OpportunityEngine — composite opportunity score combining all sub-scores.

Phase 1: only fundamental_score is available.
Phase 2: adds growth_score from dev and social metrics.
Later phases will add narrative, listing, and risk sub-scores with
their own weights.
"""

from app.exceptions import ScoringError
from app.processors.normalizer import clamp

# Phase 2 weights (must sum to 1.0)
_WEIGHT_FUNDAMENTAL = 0.60
_WEIGHT_GROWTH = 0.40


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
        if not 0.0 <= fundamental_score <= 1.0:
            raise ScoringError(
                f"OpportunityEngine: fundamental_score must be in [0, 1], got {fundamental_score}"
            )

        if growth_score is None:
            # Phase 1 behavior: only fundamental
            return clamp(fundamental_score, 0.0, 1.0)

        if not 0.0 <= growth_score <= 1.0:
            raise ScoringError(
                f"OpportunityEngine: growth_score must be in [0, 1], got {growth_score}"
            )

        # Phase 2: weighted combination
        composite = _WEIGHT_FUNDAMENTAL * fundamental_score + _WEIGHT_GROWTH * growth_score
        return clamp(composite, 0.0, 1.0)
