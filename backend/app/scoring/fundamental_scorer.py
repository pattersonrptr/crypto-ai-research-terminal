"""FundamentalScorer — static-weight fundamental score.

Phase 1: 4-metric market-data scorer (``score()``).
Phase 9: 5-sub-pillar model (``sub_pillar_score()``): technology, tokenomics,
         adoption, dev_activity, narrative — each weighted 20%.

No LLM involved. Weights can be tuned via Phase 12 backtesting.
"""

from typing import Any

from app.exceptions import ScoringError
from app.processors.normalizer import clamp, min_max_normalize

# Phase 1 — static weights that sum to 1.0
_WEIGHTS = {
    "volume_mcap_ratio": 0.30,
    "price_velocity": 0.25,
    "ath_distance_pct": 0.25,
    "market_cap_usd": 0.20,
}

# Phase 9 — 5-sub-pillar equal weights (sum to 1.0)
_SUB_PILLAR_WEIGHT = 0.20

# Rough upper bounds used for normalisation (percentile-based heuristics)
_VOLUME_MCAP_MAX = 1.0  # ratio: 100 % turnover is the ceiling
_VELOCITY_MAX = 100.0  # price change cap at ±100 %
_ATH_DIST_MAX = 99.0  # never exactly 100 % (token would be worthless)
_MCAP_MAX = 1_000_000_000_000.0  # ~$1 T (Bitcoin-scale)

_REQUIRED_FIELDS = set(_WEIGHTS.keys())


class FundamentalScorer:
    """Computes a fundamental opportunity score in [0, 1] from market features."""

    @staticmethod
    def score(data: dict[str, Any]) -> float:
        """Return a fundamental score in [0, 1] for the given market-feature dict.

        Args:
            data: Must contain ``volume_mcap_ratio``, ``price_velocity``,
                  ``ath_distance_pct``, and ``market_cap_usd``.

        Raises:
            ScoringError: If required fields are missing or ``market_cap_usd`` is negative.
        """
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"FundamentalScorer: missing fields {missing}")

        if data["market_cap_usd"] < 0:
            raise ScoringError("FundamentalScorer: market_cap_usd must be >= 0")

        vol_norm = min_max_normalize(data["volume_mcap_ratio"], 0.0, _VOLUME_MCAP_MAX)

        # price_velocity ranges from -VELOCITY_MAX to +VELOCITY_MAX; shift to [0, 1]
        vel_norm = min_max_normalize(
            clamp(data["price_velocity"], -_VELOCITY_MAX, _VELOCITY_MAX),
            -_VELOCITY_MAX,
            _VELOCITY_MAX,
        )

        ath_norm = min_max_normalize(data["ath_distance_pct"], 0.0, _ATH_DIST_MAX)
        mcap_norm = min_max_normalize(data["market_cap_usd"], 0.0, _MCAP_MAX)

        composite = (
            _WEIGHTS["volume_mcap_ratio"] * vol_norm
            + _WEIGHTS["price_velocity"] * vel_norm
            + _WEIGHTS["ath_distance_pct"] * ath_norm
            + _WEIGHTS["market_cap_usd"] * mcap_norm
        )
        return clamp(composite, 0.0, 1.0)

    @staticmethod
    def sub_pillar_score(
        *,
        technology: float,
        tokenomics: float,
        adoption: float,
        dev_activity: float,
        narrative: float,
    ) -> float:
        """Return a fundamental score from 5 sub-pillars, each weighted 20%.

        This is the Phase 9 upgrade to the original 4-metric model.
        The sub-pillar scores typically come from ``PipelineScorer`` (which
        delegates to ``HeuristicSubScorer`` or real scorers).

        Args:
            technology:  Technology quality score in [0, 1].
            tokenomics:  Tokenomics health score in [0, 1].
            adoption:    Adoption / usage score in [0, 1].
            dev_activity: Developer activity score in [0, 1].
            narrative:   Narrative / trend alignment score in [0, 1].

        Returns:
            Weighted composite in [0, 1].

        Raises:
            ScoringError: If any input is outside [0, 1].
        """
        pillars = {
            "technology": technology,
            "tokenomics": tokenomics,
            "adoption": adoption,
            "dev_activity": dev_activity,
            "narrative": narrative,
        }
        for name, value in pillars.items():
            if not 0.0 <= value <= 1.0:
                raise ScoringError(
                    f"FundamentalScorer.sub_pillar_score: {name} must be in [0, 1], got {value}"
                )

        composite = sum(v * _SUB_PILLAR_WEIGHT for v in pillars.values())
        return clamp(composite, 0.0, 1.0)
