"""ListingPredictor — ML-based listing probability prediction.

Phase 4 implementation uses a heuristic model based on weighted features.
Will be replaced with trained XGBoost model in later phases when
historical data is available for training.
"""

import math
from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class ListingPrediction:
    """Result of listing probability prediction."""

    probability: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0 (based on data completeness)

    # Feature contributions for explainability
    market_cap_contribution: float
    volume_contribution: float
    exchange_contribution: float
    social_contribution: float
    dev_contribution: float


# Feature normalization bounds (for sigmoid scaling)
_MCAP_SCALE = 100_000_000.0  # $100M = midpoint
_VOLUME_SCALE = 5_000_000.0  # $5M = midpoint
_EXCHANGE_SCALE = 5.0  # 5 exchanges = midpoint
_STARS_SCALE = 500.0  # 500 stars = midpoint
_FOLLOWERS_SCALE = 50000.0  # 50k followers = midpoint
_AGE_SCALE = 180.0  # 180 days = midpoint

# Feature weights (sum to 1.0)
_WEIGHTS = {
    "market_cap": 0.30,
    "volume": 0.20,
    "exchanges": 0.20,
    "social": 0.15,
    "dev": 0.15,
}

_REQUIRED_FIELDS = {
    "market_cap_usd",
    "volume_24h_usd",
    "exchange_count",
    "github_stars",
    "twitter_followers",
    "age_days",
}


def _sigmoid(x: float) -> float:
    """Sigmoid function mapping any value to (0, 1)."""
    return 1.0 / (1.0 + math.exp(-x))


def _normalize_feature(value: float, scale: float) -> float:
    """Normalize a feature to 0-1 range using sigmoid-like scaling.

    At value=scale, returns ~0.73 (slightly above midpoint).
    """
    if value <= 0:
        return 0.0
    # Log-scale normalization for better distribution
    log_ratio = math.log(value / scale + 1)
    return min(_sigmoid(log_ratio - 0.5), 1.0)


class ListingPredictor:
    """Predicts probability of a token getting listed on major exchanges."""

    @classmethod
    def predict(cls, features: dict[str, Any]) -> ListingPrediction:
        """Predict listing probability from token features.

        Args:
            features: Dict containing:
                - market_cap_usd: float — market capitalization
                - volume_24h_usd: float — 24h trading volume
                - exchange_count: int — number of current listings
                - github_stars: int — GitHub repository stars
                - twitter_followers: int — Twitter follower count
                - age_days: int — project age in days

        Returns:
            ListingPrediction with probability and confidence.

        Raises:
            ScoringError: If required fields are missing or invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - features.keys()
        if missing:
            raise ScoringError(f"ListingPredictor: missing fields {missing}")

        mcap = features["market_cap_usd"]
        volume = features["volume_24h_usd"]
        exchanges = features["exchange_count"]
        stars = features["github_stars"]
        followers = features["twitter_followers"]
        age = features["age_days"]

        # Validate values
        if mcap < 0:
            raise ScoringError(f"ListingPredictor: market_cap_usd must be >= 0, got {mcap}")

        # Calculate feature contributions
        mcap_contrib = _normalize_feature(mcap, _MCAP_SCALE)
        volume_contrib = _normalize_feature(volume, _VOLUME_SCALE)
        exchange_contrib = _normalize_feature(exchanges, _EXCHANGE_SCALE)
        social_contrib = _normalize_feature(followers, _FOLLOWERS_SCALE)
        dev_contrib = _normalize_feature(stars, _STARS_SCALE)

        # Age bonus: slightly boost established projects
        age_factor = min(age / _AGE_SCALE, 1.0) * 0.1  # Max 10% bonus

        # Weighted probability
        base_prob = (
            _WEIGHTS["market_cap"] * mcap_contrib
            + _WEIGHTS["volume"] * volume_contrib
            + _WEIGHTS["exchanges"] * exchange_contrib
            + _WEIGHTS["social"] * social_contrib
            + _WEIGHTS["dev"] * dev_contrib
        )

        probability = min(base_prob + age_factor, 1.0)

        # Calculate confidence based on data completeness
        non_zero_features = sum(
            1 for v in [mcap, volume, exchanges, stars, followers, age] if v > 0
        )
        confidence = non_zero_features / 6.0

        return ListingPrediction(
            probability=probability,
            confidence=confidence,
            market_cap_contribution=mcap_contrib,
            volume_contribution=volume_contrib,
            exchange_contribution=exchange_contrib,
            social_contribution=social_contrib,
            dev_contribution=dev_contrib,
        )
