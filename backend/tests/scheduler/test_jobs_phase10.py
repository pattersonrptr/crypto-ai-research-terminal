"""Tests for Phase 10 scheduler integration — narrative + cycle pipeline steps.

TDD RED phase: tests for narrative_snapshot_job and cycle-adjusted scoring
in the daily pipeline.

Note: NarrativeCluster uses ARRAY columns (PostgreSQL-only), so we use
mock sessions instead of SQLite-based integration tests.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.models.narrative import NarrativeCluster

# ---------------------------------------------------------------------------
# persist_narrative_snapshot
# ---------------------------------------------------------------------------


class TestPersistNarrativeSnapshot:
    """persist_narrative_snapshot stores NarrativeCluster rows to DB."""

    @pytest.mark.asyncio
    async def test_persists_narrative_clusters(self) -> None:
        from app.scheduler.jobs import persist_narrative_snapshot

        clusters = [
            NarrativeCluster(
                name="AI & Blockchain",
                momentum_score=8.5,
                trend="accelerating",
                keywords=["ai", "ml"],
                token_symbols=["FET", "RNDR"],
                snapshot_date=date(2026, 4, 15),
            ),
            NarrativeCluster(
                name="DeFi Lending",
                momentum_score=6.0,
                trend="stable",
                keywords=["lending"],
                token_symbols=["AAVE", "COMP"],
                snapshot_date=date(2026, 4, 15),
            ),
        ]

        session = AsyncMock()
        await persist_narrative_snapshot(clusters, session=session)

        # Should have called session.add for each cluster
        assert session.add.call_count == 2
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_clusters_noop(self) -> None:
        from app.scheduler.jobs import persist_narrative_snapshot

        session = AsyncMock()
        await persist_narrative_snapshot([], session=session)

        session.add.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_clusters_added_with_correct_names(self) -> None:
        from app.scheduler.jobs import persist_narrative_snapshot

        clusters = [
            NarrativeCluster(
                name="Meme",
                momentum_score=3.0,
                trend="declining",
                keywords=["meme"],
                token_symbols=["DOGE"],
                snapshot_date=date(2026, 5, 1),
            ),
        ]

        session = AsyncMock()
        await persist_narrative_snapshot(clusters, session=session)

        added_obj = session.add.call_args_list[0][0][0]
        assert added_obj.name == "Meme"
        assert added_obj.snapshot_date == date(2026, 5, 1)


# ---------------------------------------------------------------------------
# build_narrative_snapshot_from_categories
# ---------------------------------------------------------------------------


class TestBuildNarrativeSnapshotFromCategories:
    """build_narrative_snapshot_from_categories uses NarrativePersister."""

    def test_builds_from_token_data(self) -> None:
        from app.scheduler.jobs import build_narrative_snapshot_from_categories

        token_data: list[dict[str, Any]] = [
            {"symbol": "FET", "name": "Fetch.ai", "categories": ["ai"]},
            {"symbol": "RNDR", "name": "Render", "categories": ["ai"]},
            {"symbol": "AAVE", "name": "Aave", "categories": ["defi"]},
            {"symbol": "COMP", "name": "Compound", "categories": ["defi"]},
            {"symbol": "BTC", "name": "Bitcoin", "categories": ["layer1"]},
        ]

        clusters = build_narrative_snapshot_from_categories(
            token_data, snapshot_date=date(2026, 4, 15)
        )

        assert len(clusters) >= 2  # at least AI and DeFi (layer1 has only 1 token)
        names = {c.name for c in clusters}
        assert "AI & Machine Learning" in names
        assert "DeFi" in names

    def test_single_token_categories_skipped(self) -> None:
        from app.scheduler.jobs import build_narrative_snapshot_from_categories

        token_data: list[dict[str, Any]] = [
            {"symbol": "BTC", "name": "Bitcoin", "categories": ["layer1"]},
        ]

        clusters = build_narrative_snapshot_from_categories(
            token_data, snapshot_date=date(2026, 4, 15)
        )
        # Only 1 token in "layer1", should not create a cluster
        assert len(clusters) == 0

    def test_returns_narrative_cluster_objects(self) -> None:
        from app.scheduler.jobs import build_narrative_snapshot_from_categories

        token_data: list[dict[str, Any]] = [
            {"symbol": "FET", "name": "Fetch.ai", "categories": ["ai"]},
            {"symbol": "RNDR", "name": "Render", "categories": ["ai"]},
        ]

        clusters = build_narrative_snapshot_from_categories(
            token_data, snapshot_date=date(2026, 4, 15)
        )
        assert all(isinstance(c, NarrativeCluster) for c in clusters)
