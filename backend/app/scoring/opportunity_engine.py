"""OpportunityEngine — composite opportunity score combining all sub-scores.

Phase 1: only fundamental_score is available.
Later phases will add growth, narrative, listing, and risk sub-scores with
their own weights.
"""

from app.exceptions import ScoringError
from app.processors.normalizer import clamp


class OpportunityEngine:
    """Combines sub-scores into a single composite opportunity score in [0, 1]."""

    @staticmethod
    def composite_score(fundamental_score: float) -> float:
        """Return a composite opportunity score in [0, 1].

        Phase 1: the composite score equals the fundamental score exactly.
        Sub-score weights will evolve as more signals are added in later phases.

        Args:
            fundamental_score: A value in [0, 1] produced by ``FundamentalScorer``.

        Raises:
            ScoringError: If ``fundamental_score`` is outside [0, 1].
        """
        if not 0.0 <= fundamental_score <= 1.0:
            raise ScoringError(
                f"OpportunityEngine: fundamental_score must be in [0, 1], got {fundamental_score}"
            )
        return clamp(fundamental_score, 0.0, 1.0)
