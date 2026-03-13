"""TokenomicsRisk — evaluates token economics risk factors.

Analyzes:
- Unlock calendar (>5% unlock in 30 days = alert)
- Annual inflation rate (>10% = high)
- Circulating vs total supply ratio
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class TokenomicsRiskResult:
    """Result of tokenomics risk analysis."""

    risk_score: float  # 0.0 (healthy) to 1.0 (risky)

    # Unlock metrics
    unlock_30d_pct: float  # Percentage unlocking in next 30 days
    unlock_alert: bool  # True if >5% unlock in 30 days

    # Inflation metrics
    annual_inflation_rate: float
    high_inflation: bool  # True if >10% annual inflation

    # Supply metrics
    circulating_ratio: float  # circulating / total


# Thresholds
_UNLOCK_ALERT_THRESHOLD = 0.05  # 5% unlock in 30 days
_UNLOCK_WINDOW_DAYS = 30
_HIGH_INFLATION_THRESHOLD = 0.10  # 10% annual inflation
_LOW_CIRCULATING_THRESHOLD = 0.30  # Below 30% circulating is concerning

# Weights for risk score (sum to 1.0)
_WEIGHTS = {
    "unlock": 0.40,
    "inflation": 0.30,
    "circulating": 0.30,
}

_REQUIRED_FIELDS = {
    "circulating_supply",
    "total_supply",
    "unlock_schedule",
    "annual_inflation_rate",
}


class TokenomicsRisk:
    """Analyzes token economics for risk factors."""

    @staticmethod
    def _calculate_30d_unlock(
        unlock_schedule: list[dict[str, Any]],
    ) -> float:
        """Sum unlocks scheduled in next 30 days.

        Args:
            unlock_schedule: List of dicts with 'days_until' and 'amount_pct'.

        Returns:
            Total percentage unlocking in next 30 days.
        """
        total = 0.0
        for unlock in unlock_schedule:
            if unlock.get("days_until", float("inf")) <= _UNLOCK_WINDOW_DAYS:
                total += unlock.get("amount_pct", 0.0)
        return total

    @classmethod
    def analyze(cls, data: dict[str, Any]) -> TokenomicsRiskResult:
        """Analyze tokenomics data for risk factors.

        Args:
            data: Dict containing:
                - circulating_supply: float — current circulating supply
                - total_supply: float — total/max supply
                - unlock_schedule: list[dict] — upcoming unlocks
                - annual_inflation_rate: float — annual inflation as decimal

        Returns:
            TokenomicsRiskResult with risk_score and metrics.

        Raises:
            ScoringError: If required fields are missing or invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"TokenomicsRisk: missing fields {missing}")

        circulating = data["circulating_supply"]
        total = data["total_supply"]
        unlock_schedule = data["unlock_schedule"]
        inflation = data["annual_inflation_rate"]

        # Validate values
        if total <= 0:
            raise ScoringError(f"TokenomicsRisk: total_supply must be > 0, got {total}")
        if inflation < 0:
            raise ScoringError(
                f"TokenomicsRisk: annual_inflation_rate must be >= 0, got {inflation}"
            )
        if circulating > total:
            raise ScoringError(
                f"TokenomicsRisk: circulating_supply ({circulating}) cannot exceed "
                f"total_supply ({total})"
            )

        # Calculate metrics
        unlock_30d = cls._calculate_30d_unlock(unlock_schedule)
        unlock_alert = unlock_30d >= _UNLOCK_ALERT_THRESHOLD
        high_inflation = inflation >= _HIGH_INFLATION_THRESHOLD
        circulating_ratio = circulating / total

        # Calculate component risks (0.0-1.0 each)
        # Unlock risk: scales from 0 at 0% to 1.0 at 10%+ unlock
        unlock_risk = min(unlock_30d / 0.10, 1.0)

        # Inflation risk: scales from 0 at 0% to 1.0 at 20%+ inflation
        inflation_risk = min(inflation / 0.20, 1.0)

        # Circulating risk: low circulating ratio = more locked = more risk
        # Risk is high when circulating is low
        circulating_risk = max(0.0, 1.0 - (circulating_ratio / 0.50))

        # Weighted composite
        risk_score = (
            _WEIGHTS["unlock"] * unlock_risk
            + _WEIGHTS["inflation"] * inflation_risk
            + _WEIGHTS["circulating"] * circulating_risk
        )

        return TokenomicsRiskResult(
            risk_score=min(risk_score, 1.0),
            unlock_30d_pct=unlock_30d,
            unlock_alert=unlock_alert,
            annual_inflation_rate=inflation,
            high_inflation=high_inflation,
            circulating_ratio=circulating_ratio,
        )
