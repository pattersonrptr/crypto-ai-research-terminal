"""NarrativeTrendAnalyzer — compare narrative snapshots to classify trends.

Compares two lists of :class:`NarrativeCluster` (current vs. previous
snapshot) and produces a :class:`NarrativeTrendResult` for every narrative
in the *current* snapshot, classifying its momentum change.

Trend labels
~~~~~~~~~~~~
* **accelerating** — momentum rose by > 50 % (or narrative is new).
* **growing**      — momentum rose by 10–50 %.
* **stable**       — momentum changed by less than ±10 %.
* **declining**    — momentum dropped by more than 10 %.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.narrative import NarrativeCluster

# ---- thresholds (percentage change) -----------------------------------------
_ACCEL_THRESHOLD = 0.50  # +50 %
_GROWTH_THRESHOLD = 0.10  # +10 %
_DECLINE_THRESHOLD = -0.10  # −10 %


@dataclass(frozen=True, slots=True)
class NarrativeTrendResult:
    """Comparison result for a single narrative between two snapshots."""

    name: str
    trend: str  # accelerating | growing | stable | declining
    momentum_current: float
    momentum_previous: float
    momentum_delta: float
    is_new: bool


class NarrativeTrendAnalyzer:
    """Compare two chronological narrative snapshots and classify trends.

    All methods are static — no state is required.
    """

    @staticmethod
    def compare(
        *,
        current: list[NarrativeCluster],
        previous: list[NarrativeCluster],
    ) -> list[NarrativeTrendResult]:
        """Return trend results for every narrative present in *current*.

        Narratives that existed in *previous* but disappeared from *current*
        are simply omitted from the output.
        """
        prev_by_name: dict[str, NarrativeCluster] = {c.name: c for c in previous}
        results: list[NarrativeTrendResult] = []

        for cluster in current:
            prev = prev_by_name.get(cluster.name)

            if prev is None:
                # Brand-new narrative → always accelerating.
                results.append(
                    NarrativeTrendResult(
                        name=cluster.name,
                        trend="accelerating",
                        momentum_current=cluster.momentum_score,
                        momentum_previous=0.0,
                        momentum_delta=cluster.momentum_score,
                        is_new=True,
                    )
                )
                continue

            delta = cluster.momentum_score - prev.momentum_score
            trend = _classify_trend(prev.momentum_score, delta)

            results.append(
                NarrativeTrendResult(
                    name=cluster.name,
                    trend=trend,
                    momentum_current=cluster.momentum_score,
                    momentum_previous=prev.momentum_score,
                    momentum_delta=delta,
                    is_new=False,
                )
            )

        return results


# ---- private helpers --------------------------------------------------------


def _classify_trend(previous_momentum: float, delta: float) -> str:
    """Classify the trend label based on percentage change.

    When *previous_momentum* is zero we treat any positive delta as
    accelerating and any negative delta as declining (avoid division by zero).
    """
    if previous_momentum == 0.0:
        if delta > 0:
            return "accelerating"
        if delta < 0:
            return "declining"
        return "stable"

    pct_change = delta / abs(previous_momentum)

    if pct_change >= _ACCEL_THRESHOLD:
        return "accelerating"
    if pct_change >= _GROWTH_THRESHOLD:
        return "growing"
    if pct_change <= _DECLINE_THRESHOLD:
        return "declining"
    return "stable"
