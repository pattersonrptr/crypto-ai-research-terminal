"""ListingScorer — combines listing signals and predictions into final score.

Components:
- Signal strength from recent listings
- ML prediction probability
- Exchange breadth bonus
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class ListingScoreResult:
    """Result of listing score calculation."""

    score: float  # 0.0 to 1.0
    grade: str  # A, B, C, D, F

    # Component contributions
    signal_contribution: float
    prediction_contribution: float
    breadth_bonus: float


# Weights for components (sum to ~1.0 before bonus)
_WEIGHTS = {
    "signal": 0.40,
    "prediction": 0.50,
}

# Exchange breadth bonus parameters
_EXCHANGE_BONUS_SCALE = 10.0  # 10 exchanges = max bonus
_MAX_BREADTH_BONUS = 0.10  # Max 10% bonus from breadth

_REQUIRED_FIELDS = {
    "signal_strength",
    "prediction_probability",
    "exchange_count",
}

# Grade thresholds
_GRADE_THRESHOLDS = [
    (0.85, "A"),
    (0.70, "B"),
    (0.50, "C"),
    (0.30, "D"),
    (0.00, "F"),
]


class ListingScorer:
    """Computes listing score from signals and predictions."""

    @staticmethod
    def _assign_grade(score: float) -> str:
        """Assign letter grade based on score."""
        for threshold, grade in _GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    @classmethod
    def score(cls, data: dict[str, Any]) -> ListingScoreResult:
        """Calculate listing score from components.

        Args:
            data: Dict containing:
                - signal_strength: float (0-1) — recent listing signal strength
                - prediction_probability: float (0-1) — ML prediction
                - exchange_count: int — number of exchanges listing the token

        Returns:
            ListingScoreResult with score and grade.

        Raises:
            ScoringError: If required fields are missing or invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"ListingScorer: missing fields {missing}")

        signal = data["signal_strength"]
        prediction = data["prediction_probability"]
        exchanges = data["exchange_count"]

        # Validate ranges
        if not 0.0 <= signal <= 1.0:
            raise ScoringError(f"ListingScorer: signal_strength must be in [0, 1], got {signal}")
        if not 0.0 <= prediction <= 1.0:
            raise ScoringError(
                f"ListingScorer: prediction_probability must be in [0, 1], got {prediction}"
            )
        if exchanges < 0:
            raise ScoringError(f"ListingScorer: exchange_count must be >= 0, got {exchanges}")

        # Calculate contributions
        signal_contrib = _WEIGHTS["signal"] * signal
        prediction_contrib = _WEIGHTS["prediction"] * prediction

        # Exchange breadth bonus (capped)
        breadth_bonus = min(exchanges / _EXCHANGE_BONUS_SCALE, 1.0) * _MAX_BREADTH_BONUS

        # Final score
        total = signal_contrib + prediction_contrib + breadth_bonus
        score = min(total, 1.0)

        return ListingScoreResult(
            score=score,
            grade=cls._assign_grade(score),
            signal_contribution=signal_contrib,
            prediction_contribution=prediction_contrib,
            breadth_bonus=breadth_bonus,
        )
