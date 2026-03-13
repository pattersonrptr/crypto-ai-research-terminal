"""Tests for OpportunityEngine.

Validates composite score calculation from multiple sub-scores.
"""

import pytest

from app.exceptions import ScoringError
from app.scoring.opportunity_engine import OpportunityEngine


class TestOpportunityEngineScore:
    """OpportunityEngine.composite_score() combines sub-scores into a final [0, 1] score."""

    def test_opportunity_engine_composite_score_returns_float_between_zero_and_one(
        self,
    ) -> None:
        result = OpportunityEngine.composite_score(fundamental_score=0.7)
        assert 0.0 <= result <= 1.0

    def test_opportunity_engine_composite_score_one_equals_fundamental_at_phase_one(
        self,
    ) -> None:
        # When only fundamental_score is provided and growth_score is None,
        # the composite score equals the fundamental score exactly.
        result = OpportunityEngine.composite_score(fundamental_score=0.65)
        assert result == pytest.approx(0.65)

    def test_opportunity_engine_composite_score_zero_fundamental_returns_zero(self) -> None:
        result = OpportunityEngine.composite_score(fundamental_score=0.0)
        assert result == pytest.approx(0.0)

    def test_opportunity_engine_composite_score_raises_scoring_error_on_out_of_range(
        self,
    ) -> None:
        with pytest.raises(ScoringError):
            OpportunityEngine.composite_score(fundamental_score=1.5)

    def test_opportunity_engine_composite_score_raises_scoring_error_on_negative_input(
        self,
    ) -> None:
        with pytest.raises(ScoringError):
            OpportunityEngine.composite_score(fundamental_score=-0.1)


class TestOpportunityEngineWithGrowthScore:
    """Tests for OpportunityEngine.composite_score() with growth_score integration."""

    def test_composite_score_with_growth_score_returns_weighted_average(self) -> None:
        """When growth_score is provided, it contributes to the composite."""
        result = OpportunityEngine.composite_score(fundamental_score=0.6, growth_score=0.8)
        # Phase 2: 60% fundamental + 40% growth
        # 0.6 * 0.6 + 0.8 * 0.4 = 0.36 + 0.32 = 0.68
        assert result == pytest.approx(0.68, abs=0.01)

    def test_composite_score_with_growth_raises_on_invalid_growth(self) -> None:
        """growth_score must be in [0, 1]."""
        with pytest.raises(ScoringError):
            OpportunityEngine.composite_score(fundamental_score=0.5, growth_score=1.5)

    def test_composite_score_with_zero_growth(self) -> None:
        """Zero growth_score should lower the composite."""
        result = OpportunityEngine.composite_score(fundamental_score=0.8, growth_score=0.0)
        # 0.8 * 0.6 + 0.0 * 0.4 = 0.48
        assert result == pytest.approx(0.48, abs=0.01)

    def test_composite_score_with_high_growth_boosts_score(self) -> None:
        """High growth_score should boost the composite."""
        result_without_growth = OpportunityEngine.composite_score(fundamental_score=0.5)
        result_with_growth = OpportunityEngine.composite_score(
            fundamental_score=0.5, growth_score=1.0
        )
        assert result_with_growth > result_without_growth

    def test_composite_score_returns_range_zero_to_one(self) -> None:
        """Composite score must always be in [0, 1]."""
        result = OpportunityEngine.composite_score(fundamental_score=1.0, growth_score=1.0)
        assert 0.0 <= result <= 1.0
