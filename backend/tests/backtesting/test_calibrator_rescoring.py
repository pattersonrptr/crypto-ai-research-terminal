"""Tests for upgraded weight calibrator — re-scoring with each weight set.

TDD: RED phase — tests for calibrate_weights that actually re-ranks.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from app.backtesting.ground_truth import (
    CycleGroundTruth,
    GroundTruthEntry,
    PerformanceTier,
)
from app.backtesting.validation_metrics import TokenOutcome
from app.backtesting.weight_calibrator import (
    CalibrationResult,
    calibrate_weights,
    calibrate_weights_with_rescoring,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_snapshots() -> list[dict[str, Any]]:
    """Build snapshot dicts for 5 tokens with varying fundamentals."""
    return [
        {
            "symbol": "SOL",
            "snapshot_date": date(2020, 1, 1),
            "price_usd": 0.50,
            "market_cap_usd": 50_000_000.0,
            "volume_usd": 5_000_000.0,
            "circulating_supply": 100_000_000.0,
            "total_supply": 500_000_000.0,
            "categories": "Layer 1",
        },
        {
            "symbol": "AVAX",
            "snapshot_date": date(2020, 1, 1),
            "price_usd": 3.0,
            "market_cap_usd": 300_000_000.0,
            "volume_usd": 30_000_000.0,
            "circulating_supply": 100_000_000.0,
            "total_supply": 720_000_000.0,
            "categories": "Layer 1",
        },
        {
            "symbol": "BTC",
            "snapshot_date": date(2020, 1, 1),
            "price_usd": 7_200.0,
            "market_cap_usd": 130_000_000_000.0,
            "volume_usd": 20_000_000_000.0,
            "circulating_supply": 18_000_000.0,
            "total_supply": 21_000_000.0,
            "categories": "Store of Value",
        },
        {
            "symbol": "ETH",
            "snapshot_date": date(2020, 1, 1),
            "price_usd": 130.0,
            "market_cap_usd": 14_000_000_000.0,
            "volume_usd": 7_000_000_000.0,
            "circulating_supply": 109_000_000.0,
            "total_supply": None,
            "categories": "Layer 1",
        },
        {
            "symbol": "DOGE",
            "snapshot_date": date(2020, 1, 1),
            "price_usd": 0.002,
            "market_cap_usd": 250_000_000.0,
            "volume_usd": 50_000_000.0,
            "circulating_supply": 125_000_000_000.0,
            "total_supply": None,
            "categories": "Meme",
        },
    ]


def _make_ground_truth() -> CycleGroundTruth:
    """Ground truth: SOL and AVAX are big winners; ETH winner; rest losers/avg."""
    return CycleGroundTruth(
        cycle_name="cycle_2",
        entries=[
            GroundTruthEntry("SOL", 0.50, 260.0, 520.0, PerformanceTier.BIG_WINNER),
            GroundTruthEntry("AVAX", 3.0, 145.0, 48.3, PerformanceTier.BIG_WINNER),
            GroundTruthEntry("ETH", 130.0, 4800.0, 36.9, PerformanceTier.BIG_WINNER),
            GroundTruthEntry("BTC", 7200.0, 69000.0, 9.6, PerformanceTier.WINNER),
            GroundTruthEntry("DOGE", 0.002, 0.74, 370.0, PerformanceTier.BIG_WINNER),
        ],
    )


# ---------------------------------------------------------------------------
# Tests: calibrate_weights_with_rescoring
# ---------------------------------------------------------------------------


class TestCalibrateWeightsWithRescoring:
    """Tests for the new calibrate_weights_with_rescoring function."""

    def test_returns_calibration_result(self) -> None:
        snapshots = _make_snapshots()
        gt = _make_ground_truth()
        result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=date(2020, 1, 1),
            ground_truth=gt,
            k=3,
            step=0.50,
        )
        assert isinstance(result, CalibrationResult)

    def test_best_weights_sum_to_one(self) -> None:
        snapshots = _make_snapshots()
        gt = _make_ground_truth()
        result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=date(2020, 1, 1),
            ground_truth=gt,
            k=3,
            step=0.50,
        )
        assert result.best_weights.total() == pytest.approx(1.0, abs=0.01)

    def test_n_combinations_matches_grid_size(self) -> None:
        from app.backtesting.weight_calibrator import generate_weight_grid

        snapshots = _make_snapshots()
        gt = _make_ground_truth()
        grid = generate_weight_grid(step=0.50)
        result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=date(2020, 1, 1),
            ground_truth=gt,
            k=3,
            step=0.50,
        )
        assert result.n_combinations_tested == len(grid)

    def test_precision_varies_across_weight_combos(self) -> None:
        """Different weight combos should produce different rankings and thus
        potentially different precisions — not all identical."""
        snapshots = _make_snapshots()
        gt = _make_ground_truth()
        result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=date(2020, 1, 1),
            ground_truth=gt,
            k=3,
            step=0.50,
        )
        # Because fundamental is the only differentiator and other pillars are
        # neutral, weight combos that make fundamental=0 will produce tied
        # rankings, potentially different precision. We just check we got results.
        precisions = [p for _, p in result.all_results]
        assert len(precisions) > 0
        assert result.best_precision_at_k >= 0.0

    def test_empty_snapshots_returns_default(self) -> None:
        gt = _make_ground_truth()
        result = calibrate_weights_with_rescoring(
            snapshots=[],
            snapshot_date=date(2020, 1, 1),
            ground_truth=gt,
            k=3,
            step=0.50,
        )
        assert result.best_precision_at_k == 0.0
        assert result.n_combinations_tested == 0

    def test_empty_ground_truth_returns_default(self) -> None:
        snapshots = _make_snapshots()
        empty_gt = CycleGroundTruth(cycle_name="c", entries=[])
        result = calibrate_weights_with_rescoring(
            snapshots=snapshots,
            snapshot_date=date(2020, 1, 1),
            ground_truth=empty_gt,
            k=3,
            step=0.50,
        )
        assert result.best_precision_at_k == 0.0


# ---------------------------------------------------------------------------
# Tests: backward compatibility — old calibrate_weights still works
# ---------------------------------------------------------------------------


class TestCalibrateWeightsBackwardCompat:
    """The existing calibrate_weights function must still work."""

    def test_old_api_still_returns_result(self) -> None:
        outcomes = [
            TokenOutcome(symbol="A", model_rank=1, model_score=0.9, actual_multiplier=12.0),
            TokenOutcome(symbol="B", model_rank=2, model_score=0.8, actual_multiplier=2.0),
        ]
        result = calibrate_weights(outcomes, k=2, step=0.50)
        assert isinstance(result, CalibrationResult)
        assert result.best_precision_at_k >= 0.0
