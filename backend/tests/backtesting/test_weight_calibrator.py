"""Tests for app.backtesting.weight_calibrator — TDD Red→Green.

The weight calibrator performs a parameter sweep over pillar weights to find
the combination that maximises Precision@K on historical validation data.
"""

from __future__ import annotations

import pytest

from app.backtesting.validation_metrics import TokenOutcome
from app.backtesting.weight_calibrator import (
    CalibrationResult,
    WeightSet,
    calibrate_weights,
    generate_weight_grid,
)

# ---------------------------------------------------------------------------
# Test WeightSet
# ---------------------------------------------------------------------------


class TestWeightSet:
    """Unit tests for the WeightSet dataclass."""

    def test_weight_set_fields_are_set(self) -> None:
        """WeightSet must store all five pillar weights."""
        ws = WeightSet(
            fundamental=0.30,
            growth=0.25,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
        )
        assert ws.fundamental == pytest.approx(0.30)
        assert ws.growth == pytest.approx(0.25)
        assert ws.narrative == pytest.approx(0.20)
        assert ws.listing == pytest.approx(0.15)
        assert ws.risk == pytest.approx(0.10)

    def test_weight_set_sum_returns_total(self) -> None:
        """total() must return the sum of all weights."""
        ws = WeightSet(
            fundamental=0.30,
            growth=0.25,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
        )
        assert ws.total() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Test generate_weight_grid
# ---------------------------------------------------------------------------


class TestGenerateWeightGrid:
    """Tests for generate_weight_grid()."""

    def test_weight_grid_returns_non_empty_list(self) -> None:
        """generate_weight_grid must return at least one WeightSet."""
        grid = generate_weight_grid(step=0.25)
        assert len(grid) > 0

    def test_weight_grid_all_weights_sum_to_one(self) -> None:
        """Every WeightSet in the grid must have weights summing to ~1.0."""
        grid = generate_weight_grid(step=0.25)
        for ws in grid:
            assert ws.total() == pytest.approx(1.0, abs=0.01)

    def test_weight_grid_all_weights_non_negative(self) -> None:
        """All individual weights must be >= 0."""
        grid = generate_weight_grid(step=0.25)
        for ws in grid:
            assert ws.fundamental >= 0.0
            assert ws.growth >= 0.0
            assert ws.narrative >= 0.0
            assert ws.listing >= 0.0
            assert ws.risk >= 0.0

    def test_weight_grid_smaller_step_produces_more_combinations(self) -> None:
        """Smaller step must produce more weight combinations."""
        grid_coarse = generate_weight_grid(step=0.50)
        grid_fine = generate_weight_grid(step=0.25)
        assert len(grid_fine) > len(grid_coarse)


# ---------------------------------------------------------------------------
# Test CalibrationResult
# ---------------------------------------------------------------------------


class TestCalibrationResult:
    """Unit tests for CalibrationResult dataclass."""

    def test_calibration_result_fields_are_set(self) -> None:
        """CalibrationResult must store best_weights and best_precision."""
        ws = WeightSet(
            fundamental=0.40,
            growth=0.20,
            narrative=0.20,
            listing=0.10,
            risk=0.10,
        )
        result = CalibrationResult(
            best_weights=ws,
            best_precision_at_k=0.70,
            n_combinations_tested=56,
            all_results=[],
        )
        assert result.best_weights == ws
        assert result.best_precision_at_k == pytest.approx(0.70)
        assert result.n_combinations_tested == 56

    def test_calibration_result_improved_returns_true_when_above_baseline(self) -> None:
        """improved() must return True when best_precision > baseline."""
        ws = WeightSet(fundamental=0.4, growth=0.2, narrative=0.2, listing=0.1, risk=0.1)
        result = CalibrationResult(
            best_weights=ws,
            best_precision_at_k=0.70,
            n_combinations_tested=10,
            all_results=[],
        )
        assert result.improved(baseline_precision=0.50) is True

    def test_calibration_result_improved_returns_false_when_below_baseline(self) -> None:
        """improved() must return False when best_precision <= baseline."""
        ws = WeightSet(fundamental=0.4, growth=0.2, narrative=0.2, listing=0.1, risk=0.1)
        result = CalibrationResult(
            best_weights=ws,
            best_precision_at_k=0.40,
            n_combinations_tested=10,
            all_results=[],
        )
        assert result.improved(baseline_precision=0.50) is False


# ---------------------------------------------------------------------------
# Test calibrate_weights
# ---------------------------------------------------------------------------


class TestCalibrateWeights:
    """Tests for calibrate_weights()."""

    @staticmethod
    def _make_outcomes() -> list[TokenOutcome]:
        """Outcomes where fundamental dominance should win.

        Tokens with high vol/mcap ratios and low mcap did better in the bull run.
        """
        return [
            TokenOutcome(symbol="A", model_rank=1, model_score=0.90, actual_multiplier=12.0),
            TokenOutcome(symbol="B", model_rank=2, model_score=0.85, actual_multiplier=2.0),
            TokenOutcome(symbol="C", model_rank=3, model_score=0.80, actual_multiplier=8.0),
            TokenOutcome(symbol="D", model_rank=4, model_score=0.75, actual_multiplier=0.5),
            TokenOutcome(symbol="E", model_rank=5, model_score=0.70, actual_multiplier=6.0),
            TokenOutcome(symbol="F", model_rank=6, model_score=0.65, actual_multiplier=1.5),
            TokenOutcome(symbol="G", model_rank=7, model_score=0.60, actual_multiplier=15.0),
            TokenOutcome(symbol="H", model_rank=8, model_score=0.55, actual_multiplier=0.3),
        ]

    def test_calibrate_returns_calibration_result(self) -> None:
        """calibrate_weights must return a CalibrationResult."""
        outcomes = self._make_outcomes()
        result = calibrate_weights(outcomes, k=5, step=0.50)
        assert isinstance(result, CalibrationResult)

    def test_calibrate_best_precision_is_non_negative(self) -> None:
        """best_precision_at_k must be >= 0."""
        outcomes = self._make_outcomes()
        result = calibrate_weights(outcomes, k=5, step=0.50)
        assert result.best_precision_at_k >= 0.0

    def test_calibrate_best_weights_sum_to_one(self) -> None:
        """Best weights must sum to ~1.0."""
        outcomes = self._make_outcomes()
        result = calibrate_weights(outcomes, k=5, step=0.50)
        assert result.best_weights.total() == pytest.approx(1.0, abs=0.01)

    def test_calibrate_n_combinations_matches_grid(self) -> None:
        """n_combinations_tested must match the grid size."""
        outcomes = self._make_outcomes()
        grid = generate_weight_grid(step=0.50)
        result = calibrate_weights(outcomes, k=5, step=0.50)
        assert result.n_combinations_tested == len(grid)

    def test_calibrate_empty_outcomes_returns_default_weights(self) -> None:
        """calibrate_weights with empty outcomes must return default weights."""
        result = calibrate_weights([], k=5, step=0.50)
        assert result.best_weights.fundamental == pytest.approx(0.30)
        assert result.best_precision_at_k == pytest.approx(0.0)
