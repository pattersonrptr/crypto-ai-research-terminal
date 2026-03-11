"""FundamentalScorer — static-weight fundamental score for Phase 1.

No LLM involved at this phase. Weights will be tuned in later phases once
historical data is available for calibration.
"""

from typing import Any

from app.exceptions import ScoringError
from app.processors.normalizer import clamp, min_max_normalize

# Static weights that sum to 1.0
_WEIGHTS = {
    "volume_mcap_ratio": 0.30,
    "price_velocity": 0.25,
    "ath_distance_pct": 0.25,
    "market_cap_usd": 0.20,
}

# Rough upper bounds used for normalisation (percentile-based heuristics)
_VOLUME_MCAP_MAX = 1.0       # ratio: 100 % turnover is the ceiling
_VELOCITY_MAX = 100.0        # price change cap at ±100 %
_ATH_DIST_MAX = 99.0         # never exactly 100 % (token would be worthless)
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
