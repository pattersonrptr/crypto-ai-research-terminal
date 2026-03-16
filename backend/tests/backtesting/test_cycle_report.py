"""Tests for backtesting.cycle_report — cross-cycle analysis.

TDD: RED phase — tests for CycleReport aggregating per-cycle metrics.
"""

from __future__ import annotations

import pytest

from app.backtesting.cycle_report import (
    CycleMetrics,
    CrossCycleReport,
    build_cross_cycle_report,
)


# ---------------------------------------------------------------------------
# CycleMetrics
# ---------------------------------------------------------------------------


class TestCycleMetrics:
    """Tests for CycleMetrics dataclass."""

    def test_fields_are_set(self) -> None:
        m = CycleMetrics(
            cycle_name="cycle_1",
            precision_at_k=0.60,
            recall_at_k=0.50,
            hit_rate=0.70,
            k=10,
            n_tokens=15,
            n_winners=5,
        )
        assert m.cycle_name == "cycle_1"
        assert m.precision_at_k == pytest.approx(0.60)
        assert m.n_tokens == 15

    def test_model_is_useful_when_precision_above_50(self) -> None:
        m = CycleMetrics(
            cycle_name="c", precision_at_k=0.60, recall_at_k=0.5,
            hit_rate=0.7, k=10, n_tokens=15, n_winners=5,
        )
        assert m.model_is_useful is True

    def test_model_is_not_useful_when_precision_below_50(self) -> None:
        m = CycleMetrics(
            cycle_name="c", precision_at_k=0.30, recall_at_k=0.5,
            hit_rate=0.7, k=10, n_tokens=15, n_winners=5,
        )
        assert m.model_is_useful is False


# ---------------------------------------------------------------------------
# CrossCycleReport
# ---------------------------------------------------------------------------


class TestCrossCycleReport:
    """Tests for CrossCycleReport dataclass."""

    def test_fields_are_set(self) -> None:
        metrics = [
            CycleMetrics("c1", 0.60, 0.50, 0.70, 10, 15, 5),
            CycleMetrics("c2", 0.80, 0.60, 0.90, 10, 30, 12),
        ]
        report = CrossCycleReport(
            cycle_metrics=metrics,
            avg_precision=0.70,
            avg_recall=0.55,
            avg_hit_rate=0.80,
            consistency_score=0.85,
        )
        assert len(report.cycle_metrics) == 2
        assert report.avg_precision == pytest.approx(0.70)
        assert report.consistency_score == pytest.approx(0.85)

    def test_n_cycles(self) -> None:
        metrics = [
            CycleMetrics("c1", 0.60, 0.50, 0.70, 10, 15, 5),
            CycleMetrics("c2", 0.80, 0.60, 0.90, 10, 30, 12),
            CycleMetrics("c3", 0.70, 0.55, 0.80, 10, 50, 20),
        ]
        report = CrossCycleReport(metrics, 0.70, 0.55, 0.80, 0.90)
        assert report.n_cycles == 3


# ---------------------------------------------------------------------------
# build_cross_cycle_report
# ---------------------------------------------------------------------------


class TestBuildCrossCycleReport:
    """Tests for building a cross-cycle report from per-cycle metrics."""

    def test_report_from_two_cycles(self) -> None:
        metrics = [
            CycleMetrics("c1", 0.60, 0.40, 0.70, 10, 15, 5),
            CycleMetrics("c2", 0.80, 0.60, 0.90, 10, 30, 12),
        ]
        report = build_cross_cycle_report(metrics)
        assert isinstance(report, CrossCycleReport)
        assert report.avg_precision == pytest.approx(0.70)
        assert report.avg_recall == pytest.approx(0.50)
        assert report.avg_hit_rate == pytest.approx(0.80)

    def test_consistency_score_is_between_0_and_1(self) -> None:
        metrics = [
            CycleMetrics("c1", 0.60, 0.40, 0.70, 10, 15, 5),
            CycleMetrics("c2", 0.80, 0.60, 0.90, 10, 30, 12),
        ]
        report = build_cross_cycle_report(metrics)
        assert 0.0 <= report.consistency_score <= 1.0

    def test_perfect_consistency_with_identical_precisions(self) -> None:
        """If all cycles have the same precision, consistency should be 1.0."""
        metrics = [
            CycleMetrics("c1", 0.70, 0.50, 0.80, 10, 15, 5),
            CycleMetrics("c2", 0.70, 0.50, 0.80, 10, 30, 12),
            CycleMetrics("c3", 0.70, 0.50, 0.80, 10, 50, 20),
        ]
        report = build_cross_cycle_report(metrics)
        assert report.consistency_score == pytest.approx(1.0)

    def test_low_consistency_with_varying_precisions(self) -> None:
        """Widely varying precisions should yield lower consistency."""
        metrics = [
            CycleMetrics("c1", 0.10, 0.10, 0.20, 10, 15, 5),
            CycleMetrics("c2", 0.90, 0.90, 0.95, 10, 30, 12),
        ]
        report = build_cross_cycle_report(metrics)
        assert report.consistency_score < 0.80

    def test_single_cycle_report(self) -> None:
        metrics = [CycleMetrics("c1", 0.60, 0.50, 0.70, 10, 15, 5)]
        report = build_cross_cycle_report(metrics)
        assert report.avg_precision == pytest.approx(0.60)
        assert report.consistency_score == pytest.approx(1.0)

    def test_empty_cycles_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            build_cross_cycle_report([])
