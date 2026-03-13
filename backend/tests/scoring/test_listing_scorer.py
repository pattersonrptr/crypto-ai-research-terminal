"""Tests for ListingScorer.

Combines listing signals and predictions into a final score:
- Recent listing signal strength
- ML prediction probability
- Exchange breadth bonus
"""

import pytest

from app.scoring.listing_scorer import ListingScorer, ListingScoreResult


class TestListingScorerScore:
    """ListingScorer.score() returns a ListingScoreResult."""

    def test_listing_scorer_score_returns_result_dataclass(self) -> None:
        data = {
            "signal_strength": 0.5,
            "prediction_probability": 0.6,
            "exchange_count": 3,
        }
        result = ListingScorer.score(data)
        assert isinstance(result, ListingScoreResult)

    def test_listing_scorer_score_returns_value_between_zero_and_one(self) -> None:
        data = {
            "signal_strength": 0.5,
            "prediction_probability": 0.5,
            "exchange_count": 5,
        }
        result = ListingScorer.score(data)
        assert 0.0 <= result.score <= 1.0

    def test_listing_scorer_high_inputs_yield_high_score(self) -> None:
        """Strong signals + high prediction = high listing score."""
        data = {
            "signal_strength": 0.9,  # Recent major listing
            "prediction_probability": 0.8,  # High prediction
            "exchange_count": 8,  # Listed on many exchanges
        }
        result = ListingScorer.score(data)
        assert result.score >= 0.7

    def test_listing_scorer_low_inputs_yield_low_score(self) -> None:
        """Weak signals + low prediction = low listing score."""
        data = {
            "signal_strength": 0.1,
            "prediction_probability": 0.2,
            "exchange_count": 1,
        }
        result = ListingScorer.score(data)
        assert result.score <= 0.3


class TestListingScorerComponents:
    """ListingScorer weights components appropriately."""

    def test_listing_scorer_signal_strength_affects_score(self) -> None:
        base = {
            "signal_strength": 0.2,
            "prediction_probability": 0.5,
            "exchange_count": 3,
        }
        high_signal = {**base, "signal_strength": 0.9}

        base_result = ListingScorer.score(base)
        high_result = ListingScorer.score(high_signal)
        assert high_result.score > base_result.score

    def test_listing_scorer_prediction_affects_score(self) -> None:
        base = {
            "signal_strength": 0.5,
            "prediction_probability": 0.3,
            "exchange_count": 3,
        }
        high_pred = {**base, "prediction_probability": 0.9}

        base_result = ListingScorer.score(base)
        high_result = ListingScorer.score(high_pred)
        assert high_result.score > base_result.score

    def test_listing_scorer_exchange_count_provides_bonus(self) -> None:
        """More exchanges = higher score (breadth bonus)."""
        base = {
            "signal_strength": 0.5,
            "prediction_probability": 0.5,
            "exchange_count": 1,
        }
        many_exchanges = {**base, "exchange_count": 10}

        base_result = ListingScorer.score(base)
        many_result = ListingScorer.score(many_exchanges)
        assert many_result.score > base_result.score


class TestListingScorerGrade:
    """ListingScorer assigns grades."""

    def test_listing_scorer_assigns_grade_a(self) -> None:
        data = {
            "signal_strength": 0.95,
            "prediction_probability": 0.9,
            "exchange_count": 10,
        }
        result = ListingScorer.score(data)
        assert result.grade == "A"

    def test_listing_scorer_assigns_grade_f(self) -> None:
        data = {
            "signal_strength": 0.05,
            "prediction_probability": 0.1,
            "exchange_count": 1,
        }
        result = ListingScorer.score(data)
        assert result.grade == "F"


class TestListingScorerNoSignal:
    """ListingScorer handles missing signal data."""

    def test_listing_scorer_works_with_zero_signal(self) -> None:
        """No recent listing signal is valid input."""
        data = {
            "signal_strength": 0.0,  # No recent listing
            "prediction_probability": 0.6,
            "exchange_count": 3,
        }
        result = ListingScorer.score(data)
        assert isinstance(result, ListingScoreResult)
        assert result.score >= 0.0


class TestListingScorerValidation:
    """ListingScorer validates input data."""

    def test_listing_scorer_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            ListingScorer.score({})

    def test_listing_scorer_raises_on_signal_out_of_range(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "signal_strength": 1.5,  # > 1.0 invalid
            "prediction_probability": 0.5,
            "exchange_count": 3,
        }
        with pytest.raises(ScoringError):
            ListingScorer.score(data)

    def test_listing_scorer_raises_on_negative_exchange_count(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "signal_strength": 0.5,
            "prediction_probability": 0.5,
            "exchange_count": -1,  # Invalid
        }
        with pytest.raises(ScoringError):
            ListingScorer.score(data)
