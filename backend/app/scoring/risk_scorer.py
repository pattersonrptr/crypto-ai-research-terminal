"""RiskScorer — composite risk score from multiple risk modules.

Formula from SCOPE.md:
risk_score = (
    0.30 * rugpull_risk_inverse +
    0.25 * manipulation_risk_inverse +
    0.25 * tokenomics_risk_inverse +
    0.20 * whale_concentration_inverse
)

Where *_inverse = 1 - risk (higher = safer)
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class RiskScoreResult:
    """Result of composite risk scoring."""

    composite_score: float  # 0.0 (dangerous) to 1.0 (safe)
    grade: str  # A, B, C, D, F

    # Individual components (inverse: higher = safer)
    rugpull_inverse: float
    manipulation_inverse: float
    tokenomics_inverse: float
    whale_inverse: float


# Weights from SCOPE.md (sum to 1.0)
_WEIGHTS = {
    "rugpull": 0.30,
    "manipulation": 0.25,
    "tokenomics": 0.25,
    "whale": 0.20,
}

_REQUIRED_FIELDS = {
    "rugpull_risk",
    "manipulation_risk",
    "tokenomics_risk",
    "whale_risk",
}

# Grade thresholds (composite score -> grade)
_GRADE_THRESHOLDS = [
    (0.85, "A"),
    (0.70, "B"),
    (0.50, "C"),
    (0.30, "D"),
    (0.00, "F"),
]


class RiskScorer:
    """Computes composite risk score from individual risk components."""

    @staticmethod
    def _assign_grade(score: float) -> str:
        """Assign letter grade based on composite score."""
        for threshold, grade in _GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    @classmethod
    def score(cls, data: dict[str, Any]) -> RiskScoreResult:
        """Compute composite risk score from individual risk components.

        Args:
            data: Dict containing:
                - rugpull_risk: float (0-1) — rugpull risk score
                - manipulation_risk: float (0-1) — manipulation risk score
                - tokenomics_risk: float (0-1) — tokenomics risk score
                - whale_risk: float (0-1) — whale concentration risk score

        Returns:
            RiskScoreResult with composite_score and grade.

        Raises:
            ScoringError: If required fields are missing or values invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"RiskScorer: missing fields {missing}")

        rugpull = data["rugpull_risk"]
        manipulation = data["manipulation_risk"]
        tokenomics = data["tokenomics_risk"]
        whale = data["whale_risk"]

        # Validate ranges
        for name, value in [
            ("rugpull_risk", rugpull),
            ("manipulation_risk", manipulation),
            ("tokenomics_risk", tokenomics),
            ("whale_risk", whale),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ScoringError(f"RiskScorer: {name} must be in [0, 1], got {value}")

        # Calculate inverses (higher = safer)
        rugpull_inv = 1.0 - rugpull
        manipulation_inv = 1.0 - manipulation
        tokenomics_inv = 1.0 - tokenomics
        whale_inv = 1.0 - whale

        # Weighted composite
        composite = (
            _WEIGHTS["rugpull"] * rugpull_inv
            + _WEIGHTS["manipulation"] * manipulation_inv
            + _WEIGHTS["tokenomics"] * tokenomics_inv
            + _WEIGHTS["whale"] * whale_inv
        )

        return RiskScoreResult(
            composite_score=composite,
            grade=cls._assign_grade(composite),
            rugpull_inverse=rugpull_inv,
            manipulation_inverse=manipulation_inv,
            tokenomics_inverse=tokenomics_inv,
            whale_inverse=whale_inv,
        )
