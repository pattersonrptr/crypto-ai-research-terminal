"""Tests for NarrativeTrendAnalyzer — compare narrative snapshots over time.

TDD RED phase: tests for trend classification between two snapshot dates.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.analysis.narrative_trend import NarrativeTrendAnalyzer, NarrativeTrendResult
from app.models.narrative import NarrativeCluster


def _cluster(
    name: str,
    momentum: float,
    tokens: list[str],
    snap_date: date,
) -> NarrativeCluster:
    """Shorthand for creating a NarrativeCluster."""
    return NarrativeCluster(
        name=name,
        momentum_score=momentum,
        trend="stable",
        keywords=[name.lower()],
        token_symbols=tokens,
        snapshot_date=snap_date,
    )


# ---------------------------------------------------------------------------
# NarrativeTrendResult
# ---------------------------------------------------------------------------


class TestNarrativeTrendResult:
    """NarrativeTrendResult must carry the name, trend, and delta."""

    def test_create_trend_result(self) -> None:
        tr = NarrativeTrendResult(
            name="AI & Blockchain",
            trend="accelerating",
            momentum_current=9.0,
            momentum_previous=6.0,
            momentum_delta=3.0,
            is_new=False,
        )
        assert tr.name == "AI & Blockchain"
        assert tr.trend == "accelerating"
        assert tr.momentum_delta == 3.0
        assert tr.is_new is False

    def test_new_narrative_flagged(self) -> None:
        tr = NarrativeTrendResult(
            name="New Narrative",
            trend="accelerating",
            momentum_current=7.0,
            momentum_previous=0.0,
            momentum_delta=7.0,
            is_new=True,
        )
        assert tr.is_new is True


# ---------------------------------------------------------------------------
# NarrativeTrendAnalyzer.compare
# ---------------------------------------------------------------------------


class TestNarrativeTrendAnalyzerCompare:
    """NarrativeTrendAnalyzer.compare() classifies trends between snapshots."""

    def test_accelerating_when_momentum_increases_significantly(self) -> None:
        old = [_cluster("AI", 5.0, ["FET"], date(2026, 2, 13))]
        new = [_cluster("AI", 9.0, ["FET", "RNDR"], date(2026, 3, 15))]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)

        assert len(results) == 1
        assert results[0].trend == "accelerating"
        assert results[0].momentum_delta == pytest.approx(4.0)

    def test_growing_when_momentum_increases_moderately(self) -> None:
        old = [_cluster("AI", 6.0, ["FET"], date(2026, 2, 13))]
        new = [_cluster("AI", 7.5, ["FET"], date(2026, 3, 15))]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert results[0].trend == "growing"

    def test_stable_when_momentum_unchanged(self) -> None:
        old = [_cluster("AI", 7.0, ["FET"], date(2026, 2, 13))]
        new = [_cluster("AI", 7.2, ["FET"], date(2026, 3, 15))]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert results[0].trend == "stable"

    def test_declining_when_momentum_drops(self) -> None:
        old = [_cluster("Meme", 8.0, ["DOGE"], date(2026, 2, 13))]
        new = [_cluster("Meme", 4.0, ["DOGE"], date(2026, 3, 15))]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert results[0].trend == "declining"

    def test_new_narrative_marked_accelerating(self) -> None:
        """A narrative in current but not previous is new + accelerating."""
        old: list[NarrativeCluster] = []
        new = [_cluster("New Thing", 7.0, ["NEW"], date(2026, 3, 15))]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert len(results) == 1
        assert results[0].is_new is True
        assert results[0].trend == "accelerating"

    def test_disappeared_narrative_not_in_results(self) -> None:
        """A narrative in previous but not current is simply absent."""
        old = [_cluster("Dead Narrative", 5.0, ["DEAD"], date(2026, 2, 13))]
        new: list[NarrativeCluster] = []

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert len(results) == 0

    def test_multiple_narratives_compared(self) -> None:
        old = [
            _cluster("AI", 5.0, ["FET"], date(2026, 2, 13)),
            _cluster("DeFi", 7.0, ["AAVE"], date(2026, 2, 13)),
        ]
        new = [
            _cluster("AI", 9.0, ["FET", "RNDR"], date(2026, 3, 15)),
            _cluster("DeFi", 6.5, ["AAVE"], date(2026, 3, 15)),
            _cluster("RWA", 6.0, ["ONDO"], date(2026, 3, 15)),
        ]

        results = NarrativeTrendAnalyzer.compare(current=new, previous=old)
        assert len(results) == 3
        by_name = {r.name: r for r in results}
        assert by_name["AI"].trend == "accelerating"
        assert by_name["DeFi"].trend in ("stable", "declining")
        assert by_name["RWA"].is_new is True

    def test_empty_current_returns_empty(self) -> None:
        results = NarrativeTrendAnalyzer.compare(current=[], previous=[])
        assert results == []
