"""RugpullDetector — detects rugpull risk signals in crypto projects.

Evaluates five key risk factors:
- Anonymous/unknown team
- Wallet concentration > 30%
- Low liquidity ratio (< 1%)
- No security audit
- No GitHub repository
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class RugpullRiskResult:
    """Result of rugpull risk analysis."""

    risk_score: float  # 0.0 (safe) to 1.0 (extreme risk)

    # Individual risk flags
    anonymous_team: bool
    concentration_warning: bool  # top wallet > 30%
    liquidity_warning: bool  # liquidity ratio < 1%
    no_audit: bool
    no_github: bool


# Thresholds for risk flags
_CONCENTRATION_THRESHOLD = 0.30  # 30% of supply in top wallets
_LIQUIDITY_THRESHOLD = 0.01  # 1% liquidity ratio

# Weights for risk score calculation (sum to 1.0)
_WEIGHTS = {
    "anonymous_team": 0.25,
    "concentration": 0.25,
    "liquidity": 0.20,
    "no_audit": 0.20,
    "no_github": 0.10,
}

_REQUIRED_FIELDS = {
    "team_known",
    "top_wallet_concentration",
    "liquidity_ratio",
    "has_audit",
    "has_github",
}


class RugpullDetector:
    """Analyzes crypto projects for rugpull risk indicators."""

    @staticmethod
    def analyze(data: dict[str, Any]) -> RugpullRiskResult:
        """Analyze project data for rugpull risk signals.

        Args:
            data: Dict containing:
                - team_known: bool — whether team is publicly known
                - top_wallet_concentration: float — fraction (0-1) held by top wallets
                - liquidity_ratio: float — liquidity as fraction of market cap
                - has_audit: bool — whether project has security audit
                - has_github: bool — whether project has public GitHub

        Returns:
            RugpullRiskResult with risk_score and individual flags.

        Raises:
            ScoringError: If required fields are missing or values are invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"RugpullDetector: missing fields {missing}")

        concentration = data["top_wallet_concentration"]
        liquidity = data["liquidity_ratio"]

        # Validate value ranges
        if not 0.0 <= concentration <= 1.0:
            raise ScoringError(
                f"RugpullDetector: top_wallet_concentration must be in [0, 1], got {concentration}"
            )
        if liquidity < 0.0:
            raise ScoringError(f"RugpullDetector: liquidity_ratio must be >= 0, got {liquidity}")

        # Compute individual risk flags
        anonymous_team = not data["team_known"]
        concentration_warning = concentration > _CONCENTRATION_THRESHOLD
        liquidity_warning = liquidity < _LIQUIDITY_THRESHOLD
        no_audit = not data["has_audit"]
        no_github = not data["has_github"]

        # Compute risk scores for each factor (0.0 = safe, 1.0 = risky)
        team_risk = 1.0 if anonymous_team else 0.0
        concentration_risk = (
            min(concentration / _CONCENTRATION_THRESHOLD, 1.0) if concentration > 0 else 0.0
        )
        liquidity_risk = (
            max(0.0, 1.0 - (liquidity / _LIQUIDITY_THRESHOLD))
            if liquidity < _LIQUIDITY_THRESHOLD
            else 0.0
        )
        audit_risk = 1.0 if no_audit else 0.0
        github_risk = 1.0 if no_github else 0.0

        # Weighted composite risk score
        risk_score = (
            _WEIGHTS["anonymous_team"] * team_risk
            + _WEIGHTS["concentration"] * concentration_risk
            + _WEIGHTS["liquidity"] * liquidity_risk
            + _WEIGHTS["no_audit"] * audit_risk
            + _WEIGHTS["no_github"] * github_risk
        )

        return RugpullRiskResult(
            risk_score=min(risk_score, 1.0),
            anonymous_team=anonymous_team,
            concentration_warning=concentration_warning,
            liquidity_warning=liquidity_warning,
            no_audit=no_audit,
            no_github=no_github,
        )
