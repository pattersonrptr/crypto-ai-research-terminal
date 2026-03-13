"""Tests for RiskScorer.

Composite risk score from SCOPE.md formula:
risk_score = (
    0.30 * rugpull_risk_inverse +
    0.25 * manipulation_risk_inverse +
    0.25 * tokenomics_risk_inverse +
    0.20 * whale_concentration_inverse
)

Where *_inverse = 1 - risk (so higher = safer)
"""

import pytest

from app.scoring.risk_scorer import RiskScorer, RiskScoreResult


class TestRiskScorerScore:
    """RiskScorer.score() returns a RiskScoreResult."""

    def test_risk_scorer_score_returns_result_dataclass(self) -> None:
        data = {
            "rugpull_risk": 0.2,
            "manipulation_risk": 0.1,
            "tokenomics_risk": 0.15,
            "whale_risk": 0.1,
        }
        result = RiskScorer.score(data)
        assert isinstance(result, RiskScoreResult)

    def test_risk_scorer_score_returns_value_between_zero_and_one(self) -> None:
        data = {
            "rugpull_risk": 0.5,
            "manipulation_risk": 0.5,
            "tokenomics_risk": 0.5,
            "whale_risk": 0.5,
        }
        result = RiskScorer.score(data)
        assert 0.0 <= result.composite_score <= 1.0

    def test_risk_scorer_score_low_risks_yield_high_score(self) -> None:
        """Low individual risks = safer = higher composite score."""
        data = {
            "rugpull_risk": 0.1,
            "manipulation_risk": 0.1,
            "tokenomics_risk": 0.1,
            "whale_risk": 0.1,
        }
        result = RiskScorer.score(data)
        # With all risks at 0.1, composite should be 0.9 (inverse)
        assert result.composite_score >= 0.85

    def test_risk_scorer_score_high_risks_yield_low_score(self) -> None:
        """High individual risks = dangerous = lower composite score."""
        data = {
            "rugpull_risk": 0.9,
            "manipulation_risk": 0.9,
            "tokenomics_risk": 0.9,
            "whale_risk": 0.9,
        }
        result = RiskScorer.score(data)
        # With all risks at 0.9, composite should be 0.1
        assert result.composite_score <= 0.15


class TestRiskScorerWeights:
    """RiskScorer uses correct weights from SCOPE.md."""

    def test_risk_scorer_uses_correct_weights(self) -> None:
        """Verify weights: rugpull=0.30, manipulation=0.25, tokenomics=0.25, whale=0.20."""
        # Only rugpull_risk is 1.0, others are 0.0
        # inverse = 0, so contribution = 0.30 * 0 = 0
        # others contribute: 0.25 * 1 + 0.25 * 1 + 0.20 * 1 = 0.70
        data = {
            "rugpull_risk": 1.0,
            "manipulation_risk": 0.0,
            "tokenomics_risk": 0.0,
            "whale_risk": 0.0,
        }
        result = RiskScorer.score(data)
        expected = 0.25 * 1.0 + 0.25 * 1.0 + 0.20 * 1.0  # = 0.70
        assert abs(result.composite_score - expected) < 0.01

    def test_risk_scorer_rugpull_has_highest_weight(self) -> None:
        """Rugpull risk should have highest impact (0.30)."""
        base = {
            "rugpull_risk": 0.0,
            "manipulation_risk": 0.0,
            "tokenomics_risk": 0.0,
            "whale_risk": 0.0,
        }
        # Test impact of each component at 1.0
        rugpull_high = {**base, "rugpull_risk": 1.0}
        manip_high = {**base, "manipulation_risk": 1.0}
        token_high = {**base, "tokenomics_risk": 1.0}
        whale_high = {**base, "whale_risk": 1.0}

        # Rugpull at 1.0 should have largest negative impact
        rugpull_score = RiskScorer.score(rugpull_high).composite_score
        manip_score = RiskScorer.score(manip_high).composite_score
        token_score = RiskScorer.score(token_high).composite_score
        whale_score = RiskScorer.score(whale_high).composite_score

        # Lower score = more risk impact
        assert rugpull_score < manip_score
        assert rugpull_score < token_score
        assert rugpull_score < whale_score


class TestRiskScorerGrade:
    """RiskScorer assigns letter grades."""

    def test_risk_scorer_grade_a_for_very_safe(self) -> None:
        data = {
            "rugpull_risk": 0.05,
            "manipulation_risk": 0.05,
            "tokenomics_risk": 0.05,
            "whale_risk": 0.05,
        }
        result = RiskScorer.score(data)
        assert result.grade == "A"

    def test_risk_scorer_grade_b_for_safe(self) -> None:
        data = {
            "rugpull_risk": 0.2,
            "manipulation_risk": 0.2,
            "tokenomics_risk": 0.2,
            "whale_risk": 0.2,
        }
        result = RiskScorer.score(data)
        assert result.grade == "B"

    def test_risk_scorer_grade_c_for_moderate(self) -> None:
        data = {
            "rugpull_risk": 0.4,
            "manipulation_risk": 0.4,
            "tokenomics_risk": 0.4,
            "whale_risk": 0.4,
        }
        result = RiskScorer.score(data)
        assert result.grade == "C"

    def test_risk_scorer_grade_d_for_risky(self) -> None:
        data = {
            "rugpull_risk": 0.6,
            "manipulation_risk": 0.6,
            "tokenomics_risk": 0.6,
            "whale_risk": 0.6,
        }
        result = RiskScorer.score(data)
        assert result.grade == "D"

    def test_risk_scorer_grade_f_for_very_risky(self) -> None:
        data = {
            "rugpull_risk": 0.9,
            "manipulation_risk": 0.9,
            "tokenomics_risk": 0.9,
            "whale_risk": 0.9,
        }
        result = RiskScorer.score(data)
        assert result.grade == "F"


class TestRiskScorerValidation:
    """RiskScorer validates input data."""

    def test_risk_scorer_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            RiskScorer.score({})

    def test_risk_scorer_raises_on_risk_above_one(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "rugpull_risk": 1.5,  # Invalid
            "manipulation_risk": 0.5,
            "tokenomics_risk": 0.5,
            "whale_risk": 0.5,
        }
        with pytest.raises(ScoringError):
            RiskScorer.score(data)

    def test_risk_scorer_raises_on_negative_risk(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "rugpull_risk": -0.1,  # Invalid
            "manipulation_risk": 0.5,
            "tokenomics_risk": 0.5,
            "whale_risk": 0.5,
        }
        with pytest.raises(ScoringError):
            RiskScorer.score(data)
