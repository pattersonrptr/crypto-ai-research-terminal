"""Cross-cycle analysis report for backtesting validation.

Aggregates per-cycle validation metrics (Precision@K, Recall@K, hit rate)
and computes a consistency score that measures how stable the model performs
across different market cycles.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CycleMetrics:
    """Validation metrics for a single market cycle.

    Args:
        cycle_name: Identifier for the cycle (e.g. ``"cycle_2_2019_2021"``).
        precision_at_k: Fraction of top-K that were actual winners.
        recall_at_k: Fraction of all winners that appeared in top-K.
        hit_rate: Fraction of top-K that outperformed the market.
        k: The K value used for metrics.
        n_tokens: Total tokens evaluated in this cycle.
        n_winners: Actual winners in this cycle.
    """

    cycle_name: str
    precision_at_k: float
    recall_at_k: float
    hit_rate: float
    k: int
    n_tokens: int
    n_winners: int

    @property
    def model_is_useful(self) -> bool:
        """True when precision exceeds 50% — model beats random."""
        return self.precision_at_k > 0.5


@dataclass(frozen=True, slots=True)
class CrossCycleReport:
    """Aggregated report across multiple market cycles.

    Args:
        cycle_metrics: Per-cycle metrics list.
        avg_precision: Mean Precision@K across cycles.
        avg_recall: Mean Recall@K across cycles.
        avg_hit_rate: Mean hit rate across cycles.
        consistency_score: 1 − CV(precision) — measures how stable
            the model's precision is across cycles.  1.0 = perfectly
            consistent, 0.0 = extremely inconsistent.
    """

    cycle_metrics: list[CycleMetrics]
    avg_precision: float
    avg_recall: float
    avg_hit_rate: float
    consistency_score: float

    @property
    def n_cycles(self) -> int:
        """Number of cycles in the report."""
        return len(self.cycle_metrics)


def build_cross_cycle_report(
    cycle_metrics: list[CycleMetrics],
) -> CrossCycleReport:
    """Build a cross-cycle report from per-cycle metrics.

    The **consistency score** is defined as ``1 − CV(precision)``, where
    CV is the coefficient of variation (std / mean).  When all cycles have
    the same precision the CV is 0 and consistency is 1.0.

    Args:
        cycle_metrics: At least one :class:`CycleMetrics`.

    Returns:
        A :class:`CrossCycleReport`.

    Raises:
        ValueError: If *cycle_metrics* is empty.
    """
    if not cycle_metrics:
        msg = "cycle_metrics must contain at least one entry"
        raise ValueError(msg)

    precisions = [m.precision_at_k for m in cycle_metrics]
    recalls = [m.recall_at_k for m in cycle_metrics]
    hit_rates = [m.hit_rate for m in cycle_metrics]

    avg_p = statistics.mean(precisions)
    avg_r = statistics.mean(recalls)
    avg_h = statistics.mean(hit_rates)

    # Consistency = 1 − coefficient of variation of precision
    if len(precisions) < 2 or avg_p == 0:
        consistency = 1.0
    else:
        cv = statistics.stdev(precisions) / avg_p
        consistency = max(0.0, 1.0 - cv)

    report = CrossCycleReport(
        cycle_metrics=cycle_metrics,
        avg_precision=avg_p,
        avg_recall=avg_r,
        avg_hit_rate=avg_h,
        consistency_score=consistency,
    )

    logger.info(
        "cycle_report.built",
        n_cycles=report.n_cycles,
        avg_precision=avg_p,
        consistency=consistency,
    )
    return report
