"""Tests for HistoricalSnapshot model — cycle_tag column.

TDD: RED phase — verify cycle_tag field exists on the model.
"""

from __future__ import annotations

from datetime import date

from app.models.historical_snapshot import HistoricalSnapshot


class TestHistoricalSnapshotCycleTag:
    """Tests for the cycle_tag column on HistoricalSnapshot."""

    def test_model_has_cycle_tag_column(self) -> None:
        """HistoricalSnapshot should have a cycle_tag mapped column."""
        assert hasattr(HistoricalSnapshot, "cycle_tag")

    def test_cycle_tag_is_nullable(self) -> None:
        """cycle_tag should be optional (nullable) for backward compat."""
        col = HistoricalSnapshot.__table__.columns["cycle_tag"]
        assert col.nullable is True

    def test_cycle_tag_in_repr(self) -> None:
        snap = HistoricalSnapshot(
            symbol="BTC",
            snapshot_date=date(2020, 1, 1),
            price_usd=7200.0,
            market_cap_usd=130_000_000_000.0,
            volume_usd=25_000_000_000.0,
            cycle_tag="cycle_2_2019_2021",
        )
        assert "cycle_2_2019_2021" in repr(snap)

    def test_cycle_tag_defaults_to_none(self) -> None:
        snap = HistoricalSnapshot(
            symbol="ETH",
            snapshot_date=date(2021, 5, 1),
            price_usd=3000.0,
            market_cap_usd=350_000_000_000.0,
            volume_usd=40_000_000_000.0,
        )
        assert snap.cycle_tag is None
