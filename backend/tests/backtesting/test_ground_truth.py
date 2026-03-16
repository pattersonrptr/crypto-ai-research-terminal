"""Tests for backtesting.ground_truth — actual cycle performance data.

TDD: RED phase — tests written first.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.backtesting.ground_truth import (
    GroundTruthEntry,
    CycleGroundTruth,
    compute_roi,
    classify_performance,
    PerformanceTier,
    build_ground_truth,
)


# ---------------------------------------------------------------------------
# PerformanceTier
# ---------------------------------------------------------------------------


class TestPerformanceTier:
    """PerformanceTier enum tests."""

    def test_tier_values(self) -> None:
        assert PerformanceTier.BIG_WINNER.value == "big_winner"
        assert PerformanceTier.WINNER.value == "winner"
        assert PerformanceTier.AVERAGE.value == "average"
        assert PerformanceTier.LOSER.value == "loser"


# ---------------------------------------------------------------------------
# compute_roi
# ---------------------------------------------------------------------------


class TestComputeRoi:
    """ROI computation tests."""

    def test_roi_positive(self) -> None:
        assert compute_roi(100.0, 500.0) == pytest.approx(5.0)

    def test_roi_10x(self) -> None:
        assert compute_roi(10.0, 100.0) == pytest.approx(10.0)

    def test_roi_1x_no_change(self) -> None:
        assert compute_roi(100.0, 100.0) == pytest.approx(1.0)

    def test_roi_loss(self) -> None:
        assert compute_roi(100.0, 50.0) == pytest.approx(0.5)

    def test_roi_zero_bottom_returns_zero(self) -> None:
        assert compute_roi(0.0, 100.0) == 0.0

    def test_roi_negative_bottom_returns_zero(self) -> None:
        assert compute_roi(-1.0, 100.0) == 0.0


# ---------------------------------------------------------------------------
# classify_performance
# ---------------------------------------------------------------------------


class TestClassifyPerformance:
    """Performance tier classification tests."""

    def test_big_winner_at_10x(self) -> None:
        assert classify_performance(10.0) == PerformanceTier.BIG_WINNER

    def test_big_winner_above_10x(self) -> None:
        assert classify_performance(50.0) == PerformanceTier.BIG_WINNER

    def test_winner_at_5x(self) -> None:
        assert classify_performance(5.0) == PerformanceTier.WINNER

    def test_winner_at_9x(self) -> None:
        assert classify_performance(9.9) == PerformanceTier.WINNER

    def test_average_at_2x(self) -> None:
        assert classify_performance(2.0) == PerformanceTier.AVERAGE

    def test_average_at_4x(self) -> None:
        assert classify_performance(4.9) == PerformanceTier.AVERAGE

    def test_loser_below_1x(self) -> None:
        assert classify_performance(0.5) == PerformanceTier.LOSER

    def test_loser_at_1x(self) -> None:
        assert classify_performance(1.0) == PerformanceTier.LOSER

    def test_custom_thresholds(self) -> None:
        tier = classify_performance(3.0, winner_threshold=2.0, big_winner_threshold=5.0)
        assert tier == PerformanceTier.WINNER


# ---------------------------------------------------------------------------
# GroundTruthEntry
# ---------------------------------------------------------------------------


class TestGroundTruthEntry:
    """GroundTruthEntry dataclass tests."""

    def test_entry_fields_are_set(self) -> None:
        e = GroundTruthEntry(
            symbol="SOL",
            bottom_price=1.50,
            top_price=260.0,
            roi_multiplier=173.3,
            tier=PerformanceTier.BIG_WINNER,
        )
        assert e.symbol == "SOL"
        assert e.tier == PerformanceTier.BIG_WINNER

    def test_is_winner_true_for_winner_tier(self) -> None:
        e = GroundTruthEntry("A", 1.0, 10.0, 10.0, PerformanceTier.WINNER)
        assert e.is_winner is True

    def test_is_winner_true_for_big_winner_tier(self) -> None:
        e = GroundTruthEntry("A", 1.0, 100.0, 100.0, PerformanceTier.BIG_WINNER)
        assert e.is_winner is True

    def test_is_winner_false_for_average(self) -> None:
        e = GroundTruthEntry("A", 1.0, 3.0, 3.0, PerformanceTier.AVERAGE)
        assert e.is_winner is False


# ---------------------------------------------------------------------------
# CycleGroundTruth
# ---------------------------------------------------------------------------


class TestCycleGroundTruth:
    """CycleGroundTruth dataclass tests."""

    def test_fields_are_set(self) -> None:
        gt = CycleGroundTruth(
            cycle_name="cycle_2",
            entries=[
                GroundTruthEntry("SOL", 1.5, 260.0, 173.3, PerformanceTier.BIG_WINNER),
                GroundTruthEntry("BTC", 3200.0, 69000.0, 21.5, PerformanceTier.BIG_WINNER),
            ],
        )
        assert gt.cycle_name == "cycle_2"
        assert len(gt.entries) == 2

    def test_winners_returns_only_winners(self) -> None:
        gt = CycleGroundTruth(
            cycle_name="c",
            entries=[
                GroundTruthEntry("A", 1.0, 10.0, 10.0, PerformanceTier.BIG_WINNER),
                GroundTruthEntry("B", 1.0, 3.0, 3.0, PerformanceTier.AVERAGE),
                GroundTruthEntry("C", 1.0, 6.0, 6.0, PerformanceTier.WINNER),
            ],
        )
        winners = gt.winners
        assert len(winners) == 2
        assert {e.symbol for e in winners} == {"A", "C"}

    def test_n_winners(self) -> None:
        gt = CycleGroundTruth(
            cycle_name="c",
            entries=[
                GroundTruthEntry("A", 1.0, 10.0, 10.0, PerformanceTier.BIG_WINNER),
                GroundTruthEntry("B", 1.0, 0.5, 0.5, PerformanceTier.LOSER),
            ],
        )
        assert gt.n_winners == 1

    def test_winner_symbols(self) -> None:
        gt = CycleGroundTruth(
            cycle_name="c",
            entries=[
                GroundTruthEntry("SOL", 1.0, 10.0, 10.0, PerformanceTier.BIG_WINNER),
                GroundTruthEntry("ETH", 1.0, 8.0, 8.0, PerformanceTier.WINNER),
            ],
        )
        assert gt.winner_symbols == {"SOL", "ETH"}


# ---------------------------------------------------------------------------
# build_ground_truth
# ---------------------------------------------------------------------------


class TestBuildGroundTruth:
    """Tests for build_ground_truth from snapshot data."""

    def test_build_from_snapshots(self) -> None:
        """Build ground truth from bottom/top price snapshots."""
        bottom_prices = {"BTC": 3200.0, "SOL": 1.5, "DOGE": 0.002}
        top_prices = {"BTC": 69000.0, "SOL": 260.0, "DOGE": 0.74}

        gt = build_ground_truth("cycle_2", bottom_prices, top_prices)

        assert gt.cycle_name == "cycle_2"
        assert len(gt.entries) == 3

        sol_entry = next(e for e in gt.entries if e.symbol == "SOL")
        assert sol_entry.roi_multiplier == pytest.approx(173.33, rel=0.01)
        assert sol_entry.tier == PerformanceTier.BIG_WINNER

    def test_build_missing_top_price_excluded(self) -> None:
        """Tokens without top price are excluded from ground truth."""
        bottom = {"BTC": 3200.0, "FAKE": 1.0}
        top = {"BTC": 69000.0}
        gt = build_ground_truth("c", bottom, top)
        assert len(gt.entries) == 1
        assert gt.entries[0].symbol == "BTC"

    def test_build_zero_bottom_price_excluded(self) -> None:
        """Tokens with zero bottom price are excluded."""
        bottom = {"BTC": 0.0}
        top = {"BTC": 69000.0}
        gt = build_ground_truth("c", bottom, top)
        assert len(gt.entries) == 0

    def test_build_entries_sorted_by_roi_descending(self) -> None:
        bottom = {"A": 1.0, "B": 1.0, "C": 1.0}
        top = {"A": 5.0, "B": 20.0, "C": 10.0}
        gt = build_ground_truth("c", bottom, top)
        rois = [e.roi_multiplier for e in gt.entries]
        assert rois == sorted(rois, reverse=True)
