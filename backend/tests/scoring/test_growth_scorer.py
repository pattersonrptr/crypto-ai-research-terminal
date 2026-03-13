"""TDD tests for GrowthScorer — composite growth score from dev and social metrics."""

import pytest

from app.exceptions import ScoringError
from app.scoring.growth_scorer import GrowthScorer


class TestGrowthScorerScore:
    """Tests for GrowthScorer.score() method."""

    def test_score_returns_value_in_range(self) -> None:
        """score() returns a value between 0.0 and 1.0."""
        data = {
            "dev_activity_score": 0.5,
            "commit_growth_pct": 20.0,
            "contributor_growth_pct": 10.0,
            "social_engagement_score": 0.6,
            "subscriber_growth_pct": 5.0,
            "mention_growth_pct": 15.0,
        }
        result = GrowthScorer.score(data)
        assert 0.0 <= result <= 1.0

    def test_score_high_growth(self) -> None:
        """score() returns high value for strong growth across all metrics."""
        data = {
            "dev_activity_score": 0.9,
            "commit_growth_pct": 50.0,
            "contributor_growth_pct": 30.0,
            "social_engagement_score": 0.85,
            "subscriber_growth_pct": 20.0,
            "mention_growth_pct": 100.0,
        }
        result = GrowthScorer.score(data)
        assert result >= 0.7

    def test_score_low_growth(self) -> None:
        """score() returns low value for stagnant or declining metrics."""
        data = {
            "dev_activity_score": 0.1,
            "commit_growth_pct": -10.0,
            "contributor_growth_pct": -5.0,
            "social_engagement_score": 0.1,
            "subscriber_growth_pct": -2.0,
            "mention_growth_pct": -20.0,
        }
        result = GrowthScorer.score(data)
        assert result <= 0.3

    def test_score_zero_input(self) -> None:
        """score() handles zero values gracefully."""
        data = {
            "dev_activity_score": 0.0,
            "commit_growth_pct": 0.0,
            "contributor_growth_pct": 0.0,
            "social_engagement_score": 0.0,
            "subscriber_growth_pct": 0.0,
            "mention_growth_pct": 0.0,
        }
        result = GrowthScorer.score(data)
        # All zeros should give roughly 0.5 for growth percentages (normalized midpoint)
        # and 0.0 for absolute scores
        assert 0.0 <= result <= 0.5


class TestGrowthScorerValidation:
    """Tests for GrowthScorer validation."""

    def test_score_missing_field_raises_error(self) -> None:
        """score() raises ScoringError when required fields are missing."""
        data = {
            "dev_activity_score": 0.5,
            # Missing other fields
        }
        with pytest.raises(ScoringError) as exc_info:
            GrowthScorer.score(data)
        assert "missing" in str(exc_info.value).lower()

    def test_score_partial_fields_raises_error(self) -> None:
        """score() raises ScoringError when only some fields provided."""
        data = {
            "dev_activity_score": 0.5,
            "commit_growth_pct": 20.0,
            "contributor_growth_pct": 10.0,
            # Missing social fields
        }
        with pytest.raises(ScoringError):
            GrowthScorer.score(data)


class TestGrowthScorerWeights:
    """Tests for GrowthScorer weighting behavior."""

    def test_dev_activity_has_significant_weight(self) -> None:
        """dev_activity_score should have significant impact on total score."""
        base = {
            "dev_activity_score": 0.0,
            "commit_growth_pct": 0.0,
            "contributor_growth_pct": 0.0,
            "social_engagement_score": 0.0,
            "subscriber_growth_pct": 0.0,
            "mention_growth_pct": 0.0,
        }
        high_dev = {**base, "dev_activity_score": 1.0}
        low_dev = {**base, "dev_activity_score": 0.0}

        diff = GrowthScorer.score(high_dev) - GrowthScorer.score(low_dev)
        # dev_activity should contribute at least 15% of the total score range
        assert diff >= 0.15

    def test_social_engagement_has_significant_weight(self) -> None:
        """social_engagement_score should have significant impact on total score."""
        base = {
            "dev_activity_score": 0.0,
            "commit_growth_pct": 0.0,
            "contributor_growth_pct": 0.0,
            "social_engagement_score": 0.0,
            "subscriber_growth_pct": 0.0,
            "mention_growth_pct": 0.0,
        }
        high_social = {**base, "social_engagement_score": 1.0}
        low_social = {**base, "social_engagement_score": 0.0}

        diff = GrowthScorer.score(high_social) - GrowthScorer.score(low_social)
        # social_engagement should contribute at least 15% of the total score range
        assert diff >= 0.15
