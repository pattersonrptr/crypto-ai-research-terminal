"""GrowthScorer — composite growth score from dev and social metrics.

Combines development activity and social engagement metrics into a single
growth signal score. Higher scores indicate projects with strong momentum.
"""

from typing import Any

from app.exceptions import ScoringError
from app.processors.normalizer import clamp, min_max_normalize

# Static weights that sum to 1.0
# Development metrics: 50%, Social metrics: 50%
_WEIGHTS = {
    "dev_activity_score": 0.20,  # Already normalized 0-1
    "commit_growth_pct": 0.15,  # Growth percentage
    "contributor_growth_pct": 0.15,  # Growth percentage
    "social_engagement_score": 0.20,  # Already normalized 0-1
    "subscriber_growth_pct": 0.15,  # Growth percentage
    "mention_growth_pct": 0.15,  # Growth percentage
}

# Growth percentage normalization bounds
_GROWTH_MIN = -50.0  # -50% is significant decline
_GROWTH_MAX = 100.0  # +100% is exceptional growth

_REQUIRED_FIELDS = set(_WEIGHTS.keys())


class GrowthScorer:
    """Computes a composite growth score in [0, 1] from dev and social metrics."""

    @staticmethod
    def score(data: dict[str, Any]) -> float:
        """Return a growth score in [0, 1] for the given metrics dict.

        Args:
            data: Must contain ``dev_activity_score``, ``commit_growth_pct``,
                  ``contributor_growth_pct``, ``social_engagement_score``,
                  ``subscriber_growth_pct``, and ``mention_growth_pct``.

        Raises:
            ScoringError: If required fields are missing.

        Returns:
            Growth score between 0.0 and 1.0.
        """
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"GrowthScorer: missing fields {missing}")

        # Dev activity score is already normalized 0-1
        dev_activity_norm = clamp(data["dev_activity_score"], 0.0, 1.0)

        # Growth percentages: normalize from [-50%, +100%] to [0, 1]
        commit_growth_norm = min_max_normalize(
            clamp(data["commit_growth_pct"], _GROWTH_MIN, _GROWTH_MAX),
            _GROWTH_MIN,
            _GROWTH_MAX,
        )
        contributor_growth_norm = min_max_normalize(
            clamp(data["contributor_growth_pct"], _GROWTH_MIN, _GROWTH_MAX),
            _GROWTH_MIN,
            _GROWTH_MAX,
        )

        # Social engagement score is already normalized 0-1
        social_engagement_norm = clamp(data["social_engagement_score"], 0.0, 1.0)

        # Social growth percentages
        subscriber_growth_norm = min_max_normalize(
            clamp(data["subscriber_growth_pct"], _GROWTH_MIN, _GROWTH_MAX),
            _GROWTH_MIN,
            _GROWTH_MAX,
        )
        mention_growth_norm = min_max_normalize(
            clamp(data["mention_growth_pct"], _GROWTH_MIN, _GROWTH_MAX),
            _GROWTH_MIN,
            _GROWTH_MAX,
        )

        composite = (
            _WEIGHTS["dev_activity_score"] * dev_activity_norm
            + _WEIGHTS["commit_growth_pct"] * commit_growth_norm
            + _WEIGHTS["contributor_growth_pct"] * contributor_growth_norm
            + _WEIGHTS["social_engagement_score"] * social_engagement_norm
            + _WEIGHTS["subscriber_growth_pct"] * subscriber_growth_norm
            + _WEIGHTS["mention_growth_pct"] * mention_growth_norm
        )
        return clamp(composite, 0.0, 1.0)
