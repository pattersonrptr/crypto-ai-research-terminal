"""Tests for OpportunityEngine Phase 10 — cycle-aware scoring.

TDD RED phase: OpportunityEngine should adjust scores based on cycle phase.
"""

from __future__ import annotations

import pytest

from app.analysis.cycle_detector import CyclePhase
from app.scoring.opportunity_engine import OpportunityEngine


class TestCycleAdjustedScore:
    """OpportunityEngine.cycle_adjusted_score() applies cycle multiplier."""

    def test_bull_phase_boosts_score(self) -> None:
        base = 0.5
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.BULL)
        assert adjusted > base

    def test_bear_phase_dampens_score(self) -> None:
        base = 0.5
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.BEAR)
        assert adjusted < base

    def test_accumulation_phase_neutral(self) -> None:
        base = 0.5
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.ACCUMULATION)
        assert adjusted == pytest.approx(base)

    def test_distribution_phase_slight_dampen(self) -> None:
        base = 0.5
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.DISTRIBUTION)
        assert adjusted < base

    def test_result_clamped_to_0_1(self) -> None:
        """Even with bull boost, score should not exceed 1.0."""
        adjusted = OpportunityEngine.cycle_adjusted_score(0.99, CyclePhase.BULL)
        assert 0.0 <= adjusted <= 1.0

    def test_zero_base_stays_zero(self) -> None:
        adjusted = OpportunityEngine.cycle_adjusted_score(0.0, CyclePhase.BULL)
        assert adjusted == 0.0

    def test_none_phase_returns_base_unchanged(self) -> None:
        """When phase is None (unavailable), return base score."""
        base = 0.5
        adjusted = OpportunityEngine.cycle_adjusted_score(base, None)
        assert adjusted == base
