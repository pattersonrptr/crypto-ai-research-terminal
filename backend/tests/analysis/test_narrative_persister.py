"""Tests for NarrativePersister — saves NarrativeDetector output to DB.

TDD: tests for converting detected narratives into NarrativeCluster rows
and persisting them. Uses pure unit tests (no DB) — persistence is tested
by verifying the service produces the correct ORM objects.
"""

from __future__ import annotations

from datetime import date

from app.ai.narrative_detector import Narrative, NarrativeDetectorResult
from app.analysis.narrative_persister import NarrativePersister

# ---------------------------------------------------------------------------
# NarrativePersister.to_clusters
# ---------------------------------------------------------------------------


class TestNarrativePersisterToClusters:
    """NarrativePersister.to_clusters() converts detector output to ORM rows."""

    def test_converts_single_narrative(self) -> None:
        result = NarrativeDetectorResult(
            narratives=[
                Narrative(
                    name="AI & Blockchain",
                    momentum_score=8.5,
                    trend="accelerating",
                    tokens=["FET", "RNDR", "TAO"],
                    keywords=["AI agents", "GPU compute"],
                ),
            ]
        )
        clusters = NarrativePersister.to_clusters(result, snapshot_date=date(2026, 3, 15))

        assert len(clusters) == 1
        c = clusters[0]
        assert c.name == "AI & Blockchain"
        assert c.momentum_score == 8.5
        assert c.trend == "accelerating"
        assert c.token_symbols == ["FET", "RNDR", "TAO"]
        assert c.keywords == ["AI agents", "GPU compute"]
        assert c.snapshot_date == date(2026, 3, 15)

    def test_converts_multiple_narratives(self) -> None:
        result = NarrativeDetectorResult(
            narratives=[
                Narrative(
                    name="AI",
                    momentum_score=9.0,
                    trend="accelerating",
                    tokens=["FET"],
                    keywords=["AI"],
                ),
                Narrative(
                    name="Layer 2",
                    momentum_score=7.0,
                    trend="stable",
                    tokens=["ARB", "OP"],
                    keywords=["rollups", "L2"],
                ),
                Narrative(
                    name="RWA",
                    momentum_score=6.5,
                    trend="growing",
                    tokens=["ONDO"],
                    keywords=["tokenised assets"],
                ),
            ]
        )
        clusters = NarrativePersister.to_clusters(result, snapshot_date=date(2026, 3, 15))
        assert len(clusters) == 3
        assert [c.name for c in clusters] == ["AI", "Layer 2", "RWA"]

    def test_empty_result_returns_empty_list(self) -> None:
        result = NarrativeDetectorResult(narratives=[])
        clusters = NarrativePersister.to_clusters(result, snapshot_date=date(2026, 3, 15))
        assert clusters == []

    def test_momentum_score_clamped_to_10(self) -> None:
        """Momentum scores above 10 should be clamped."""
        result = NarrativeDetectorResult(
            narratives=[
                Narrative(
                    name="Hype",
                    momentum_score=15.0,
                    trend="accelerating",
                    tokens=["HYPE"],
                    keywords=["hype"],
                ),
            ]
        )
        clusters = NarrativePersister.to_clusters(result, snapshot_date=date(2026, 3, 15))
        assert clusters[0].momentum_score == 10.0


# ---------------------------------------------------------------------------
# NarrativePersister.build_seed_narratives — fallback from market data
# ---------------------------------------------------------------------------


class TestBuildSeedNarratives:
    """When NarrativeDetector can't run (no social data), build from market data."""

    def test_build_from_token_categories(self) -> None:
        """Build basic narratives from token category metadata."""
        token_data = [
            {"symbol": "FET", "categories": ["AI", "Machine Learning"]},
            {"symbol": "RNDR", "categories": ["AI", "GPU"]},
            {"symbol": "TAO", "categories": ["AI"]},
            {"symbol": "ARB", "categories": ["Layer 2", "Ethereum Ecosystem"]},
            {"symbol": "OP", "categories": ["Layer 2", "Ethereum Ecosystem"]},
            {"symbol": "AAVE", "categories": ["DeFi", "Lending"]},
        ]
        clusters = NarrativePersister.build_from_categories(
            token_data, snapshot_date=date(2026, 3, 15)
        )
        assert len(clusters) >= 2  # At least AI and Layer 2

        # AI narrative should contain FET, RNDR, TAO
        ai_narrative = next((c for c in clusters if "AI" in c.name.upper()), None)
        assert ai_narrative is not None
        assert "FET" in ai_narrative.token_symbols
        assert "RNDR" in ai_narrative.token_symbols

    def test_build_empty_token_data(self) -> None:
        clusters = NarrativePersister.build_from_categories([], snapshot_date=date(2026, 3, 15))
        assert clusters == []

    def test_tokens_without_categories_skipped(self) -> None:
        token_data = [
            {"symbol": "UNKNOWN", "categories": []},
            {"symbol": "FET", "categories": ["AI"]},
        ]
        clusters = NarrativePersister.build_from_categories(
            token_data, snapshot_date=date(2026, 3, 15)
        )
        # Only AI narrative, not an "empty" one
        assert all(len(c.token_symbols) > 0 for c in clusters)

    def test_minimum_tokens_per_narrative(self) -> None:
        """Narratives with fewer than 2 tokens are excluded."""
        token_data = [
            {"symbol": "FET", "categories": ["AI"]},
            {"symbol": "RNDR", "categories": ["AI"]},
            {"symbol": "LONELY", "categories": ["ObscureNarrative"]},
        ]
        clusters = NarrativePersister.build_from_categories(
            token_data, snapshot_date=date(2026, 3, 15)
        )
        names = [c.name for c in clusters]
        assert "ObscureNarrative" not in names
