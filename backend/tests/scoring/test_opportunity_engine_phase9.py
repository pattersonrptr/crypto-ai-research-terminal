"""Tests for OpportunityEngine Phase 9 — full 5-pillar composite formula.

These tests validate the new `full_composite_score` method that combines all
sub-scores using the 5-pillar formula from SCOPE.md §9.
"""

import pytest

from app.exceptions import ScoringError
from app.scoring.opportunity_engine import OpportunityEngine


class TestFullCompositeScore:
    """OpportunityEngine.full_composite_score() — 5-pillar formula."""

    def test_full_composite_returns_float_in_range(self) -> None:
        result = OpportunityEngine.full_composite_score(
            fundamental=0.7,
            growth=0.6,
            narrative=0.5,
            listing=0.4,
            risk=0.8,
        )
        assert 0.0 <= result <= 1.0

    def test_full_composite_weights_sum_correctly(self) -> None:
        """With all inputs at 1.0, composite should be 1.0."""
        result = OpportunityEngine.full_composite_score(
            fundamental=1.0,
            growth=1.0,
            narrative=1.0,
            listing=1.0,
            risk=1.0,
        )
        assert result == pytest.approx(1.0, abs=0.01)

    def test_full_composite_all_zeros(self) -> None:
        result = OpportunityEngine.full_composite_score(
            fundamental=0.0,
            growth=0.0,
            narrative=0.0,
            listing=0.0,
            risk=0.0,
        )
        assert result == pytest.approx(0.0, abs=0.01)

    def test_full_composite_fundamental_has_highest_weight(self) -> None:
        """Fundamental at 1.0, others at 0 → should be approximately 0.30."""
        result = OpportunityEngine.full_composite_score(
            fundamental=1.0,
            growth=0.0,
            narrative=0.0,
            listing=0.0,
            risk=0.0,
        )
        assert 0.25 <= result <= 0.35

    def test_full_composite_raises_on_out_of_range(self) -> None:
        with pytest.raises(ScoringError):
            OpportunityEngine.full_composite_score(
                fundamental=1.5,
                growth=0.5,
                narrative=0.5,
                listing=0.5,
                risk=0.5,
            )

    def test_full_composite_raises_on_negative(self) -> None:
        with pytest.raises(ScoringError):
            OpportunityEngine.full_composite_score(
                fundamental=0.5,
                growth=-0.1,
                narrative=0.5,
                listing=0.5,
                risk=0.5,
            )

    def test_full_composite_with_cycle_leader_boost(self) -> None:
        """cycle_leader_prob > 0 should amplify the composite up to 10%."""
        base = OpportunityEngine.full_composite_score(
            fundamental=0.6,
            growth=0.5,
            narrative=0.4,
            listing=0.3,
            risk=0.7,
        )
        boosted = OpportunityEngine.full_composite_score(
            fundamental=0.6,
            growth=0.5,
            narrative=0.4,
            listing=0.3,
            risk=0.7,
            cycle_leader_prob=0.9,
        )
        assert boosted > base
        # Boost capped at 10%
        assert boosted <= base * 1.10 + 0.001

    def test_full_composite_no_boost_when_cycle_leader_zero(self) -> None:
        base = OpportunityEngine.full_composite_score(
            fundamental=0.6,
            growth=0.5,
            narrative=0.4,
            listing=0.3,
            risk=0.7,
        )
        no_boost = OpportunityEngine.full_composite_score(
            fundamental=0.6,
            growth=0.5,
            narrative=0.4,
            listing=0.3,
            risk=0.7,
            cycle_leader_prob=0.0,
        )
        assert base == pytest.approx(no_boost, abs=0.001)


class TestBackwardCompatibility:
    """Existing composite_score() must still work for backward compatibility."""

    def test_phase1_mode_still_works(self) -> None:
        result = OpportunityEngine.composite_score(fundamental_score=0.7)
        assert result == pytest.approx(0.7, abs=0.01)

    def test_phase2_mode_still_works(self) -> None:
        result = OpportunityEngine.composite_score(fundamental_score=0.6, growth_score=0.8)
        assert result == pytest.approx(0.68, abs=0.01)
