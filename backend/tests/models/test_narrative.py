"""Tests for NarrativeCluster ORM model and NarrativePersister service.

TDD RED phase: write failing tests for narrative persistence pipeline.
"""

from __future__ import annotations

from datetime import date

from app.models.narrative import NarrativeCluster

# ---------------------------------------------------------------------------
# NarrativeCluster ORM model
# ---------------------------------------------------------------------------


class TestNarrativeClusterModel:
    """NarrativeCluster model must match the ``narratives`` table schema."""

    def test_tablename_is_narratives(self) -> None:
        assert NarrativeCluster.__tablename__ == "narratives"

    def test_model_has_required_columns(self) -> None:
        """All SCOPE.md §5 columns must be present."""
        mapper = NarrativeCluster.__table__.columns
        expected = {
            "id",
            "name",
            "momentum_score",
            "trend",
            "keywords",
            "token_symbols",
            "snapshot_date",
            "created_at",
        }
        assert expected.issubset({c.name for c in mapper})

    def test_create_narrative_cluster(self) -> None:
        narrative = NarrativeCluster(
            name="AI & Blockchain",
            momentum_score=8.5,
            trend="accelerating",
            keywords=["AI agents", "GPU compute"],
            token_symbols=["FET", "RNDR", "TAO"],
            snapshot_date=date(2025, 7, 22),
        )
        assert narrative.name == "AI & Blockchain"
        assert narrative.momentum_score == 8.5
        assert narrative.trend == "accelerating"
        assert narrative.keywords == ["AI agents", "GPU compute"]
        assert narrative.token_symbols == ["FET", "RNDR", "TAO"]
        assert narrative.snapshot_date == date(2025, 7, 22)

    def test_repr(self) -> None:
        narrative = NarrativeCluster(
            id=1,
            name="AI & Blockchain",
            momentum_score=8.5,
            trend="accelerating",
        )
        r = repr(narrative)
        assert "NarrativeCluster" in r
        assert "AI & Blockchain" in r
