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
        # In Phase 1, only fundamental_score is available.
        # The composite score must equal the fundamental score exactly.
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
