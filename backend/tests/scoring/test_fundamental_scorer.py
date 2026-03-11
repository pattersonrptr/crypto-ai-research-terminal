"""Tests for FundamentalScorer.

Uses static weights — no LLM involved at this phase.
"""

import pytest

from app.exceptions import ScoringError
from app.scoring.fundamental_scorer import FundamentalScorer


class TestFundamentalScorerScore:
    """FundamentalScorer.score() returns a float in [0, 1]."""

    def test_fundamental_scorer_score_returns_float_between_zero_and_one(self) -> None:
        data = {
            "volume_mcap_ratio": 0.1,
            "price_velocity": 5.0,
            "ath_distance_pct": 50.0,
            "market_cap_usd": 1_000_000_000.0,
        }
        result = FundamentalScorer.score(data)
        assert 0.0 <= result <= 1.0

    def test_fundamental_scorer_score_high_quality_data_scores_higher(self) -> None:
        strong = {
            "volume_mcap_ratio": 0.3,
            "price_velocity": 20.0,
            "ath_distance_pct": 80.0,
            "market_cap_usd": 5_000_000_000.0,
        }
        weak = {
            "volume_mcap_ratio": 0.01,
            "price_velocity": -20.0,
            "ath_distance_pct": 5.0,
            "market_cap_usd": 100_000.0,
        }
        assert FundamentalScorer.score(strong) > FundamentalScorer.score(weak)

    def test_fundamental_scorer_score_raises_scoring_error_on_missing_fields(self) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.score({})

    def test_fundamental_scorer_score_raises_scoring_error_on_negative_market_cap(
        self,
    ) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.score(
                {
                    "volume_mcap_ratio": 0.1,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 30.0,
                    "market_cap_usd": -1.0,
                }
            )
