"""Tests for RugpullDetector.

Detects rugpull risk signals:
- Anonymous/unknown team
- Wallet concentration > 30%
- Low liquidity ratio
- No security audit
- No GitHub repository
"""

import pytest

from app.risk.rugpull_detector import RugpullDetector, RugpullRiskResult


class TestRugpullDetectorAnalyze:
    """RugpullDetector.analyze() returns a RugpullRiskResult."""

    def test_rugpull_detector_analyze_returns_result_dataclass(self) -> None:
        data = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        result = RugpullDetector.analyze(data)
        assert isinstance(result, RugpullRiskResult)

    def test_rugpull_detector_analyze_low_risk_project_scores_low(self) -> None:
        """Safe project: known team, low concentration, good liquidity, audited, has GitHub."""
        data = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        result = RugpullDetector.analyze(data)
        assert 0.0 <= result.risk_score <= 0.3

    def test_rugpull_detector_analyze_high_risk_project_scores_high(self) -> None:
        """Risky project: anonymous, high concentration, no liquidity, no audit, no GitHub."""
        data = {
            "team_known": False,
            "top_wallet_concentration": 0.50,
            "liquidity_ratio": 0.001,
            "has_audit": False,
            "has_github": False,
        }
        result = RugpullDetector.analyze(data)
        assert result.risk_score >= 0.7

    def test_rugpull_detector_analyze_anonymous_team_increases_risk(self) -> None:
        base = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        anonymous = {**base, "team_known": False}
        base_score = RugpullDetector.analyze(base).risk_score
        anonymous_score = RugpullDetector.analyze(anonymous).risk_score
        assert anonymous_score > base_score

    def test_rugpull_detector_analyze_high_concentration_increases_risk(self) -> None:
        base = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        concentrated = {**base, "top_wallet_concentration": 0.40}
        base_score = RugpullDetector.analyze(base).risk_score
        concentrated_score = RugpullDetector.analyze(concentrated).risk_score
        assert concentrated_score > base_score

    def test_rugpull_detector_analyze_low_liquidity_increases_risk(self) -> None:
        base = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        illiquid = {**base, "liquidity_ratio": 0.001}
        base_score = RugpullDetector.analyze(base).risk_score
        illiquid_score = RugpullDetector.analyze(illiquid).risk_score
        assert illiquid_score > base_score

    def test_rugpull_detector_analyze_no_audit_increases_risk(self) -> None:
        base = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        unaudited = {**base, "has_audit": False}
        base_score = RugpullDetector.analyze(base).risk_score
        unaudited_score = RugpullDetector.analyze(unaudited).risk_score
        assert unaudited_score > base_score

    def test_rugpull_detector_analyze_no_github_increases_risk(self) -> None:
        base = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        no_github = {**base, "has_github": False}
        base_score = RugpullDetector.analyze(base).risk_score
        no_github_score = RugpullDetector.analyze(no_github).risk_score
        assert no_github_score > base_score


class TestRugpullDetectorFlags:
    """RugpullRiskResult contains individual risk flags."""

    def test_rugpull_detector_flags_concentration_warning_above_threshold(self) -> None:
        data = {
            "team_known": True,
            "top_wallet_concentration": 0.35,  # > 30% threshold
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        result = RugpullDetector.analyze(data)
        assert result.concentration_warning is True

    def test_rugpull_detector_flags_concentration_warning_below_threshold(self) -> None:
        data = {
            "team_known": True,
            "top_wallet_concentration": 0.25,  # < 30% threshold
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        result = RugpullDetector.analyze(data)
        assert result.concentration_warning is False

    def test_rugpull_detector_flags_liquidity_warning_below_threshold(self) -> None:
        data = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": 0.005,  # < 1% threshold
            "has_audit": True,
            "has_github": True,
        }
        result = RugpullDetector.analyze(data)
        assert result.liquidity_warning is True

    def test_rugpull_detector_flags_all_signals_present(self) -> None:
        """All red flags should be captured."""
        data = {
            "team_known": False,
            "top_wallet_concentration": 0.50,
            "liquidity_ratio": 0.001,
            "has_audit": False,
            "has_github": False,
        }
        result = RugpullDetector.analyze(data)
        assert result.anonymous_team is True
        assert result.concentration_warning is True
        assert result.liquidity_warning is True
        assert result.no_audit is True
        assert result.no_github is True


class TestRugpullDetectorValidation:
    """RugpullDetector validates input data."""

    def test_rugpull_detector_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            RugpullDetector.analyze({})

    def test_rugpull_detector_raises_on_invalid_concentration(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "team_known": True,
            "top_wallet_concentration": 1.5,  # > 1.0 invalid
            "liquidity_ratio": 0.05,
            "has_audit": True,
            "has_github": True,
        }
        with pytest.raises(ScoringError):
            RugpullDetector.analyze(data)

    def test_rugpull_detector_raises_on_negative_liquidity(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "team_known": True,
            "top_wallet_concentration": 0.10,
            "liquidity_ratio": -0.01,  # negative invalid
            "has_audit": True,
            "has_github": True,
        }
        with pytest.raises(ScoringError):
            RugpullDetector.analyze(data)
