"""Tests for app.models.historical_snapshot — TDD Red→Green."""

from __future__ import annotations

from datetime import date

from app.models.historical_snapshot import HistoricalSnapshot


class TestHistoricalSnapshotFields:
    """Unit tests for HistoricalSnapshot ORM model field definitions."""

    def test_historical_snapshot_tablename_is_historical_snapshots(self) -> None:
        """HistoricalSnapshot.__tablename__ must be 'historical_snapshots'."""
        assert HistoricalSnapshot.__tablename__ == "historical_snapshots"

    def test_historical_snapshot_has_required_columns(self) -> None:
        """Model must expose symbol, snapshot_date, price_usd, market_cap, volume."""
        columns = {c.name for c in HistoricalSnapshot.__table__.columns}
        expected = {
            "id",
            "symbol",
            "snapshot_date",
            "price_usd",
            "market_cap_usd",
            "volume_usd",
            "circulating_supply",
            "total_supply",
            "categories",
            "collected_at",
        }
        assert expected.issubset(columns)

    def test_historical_snapshot_unique_constraint_on_symbol_and_date(self) -> None:
        """Model must define a unique constraint on (symbol, snapshot_date)."""
        constraint_names = [
            c.name for c in HistoricalSnapshot.__table__.constraints if hasattr(c, "name")
        ]
        assert any("uq_hist_snapshot_symbol_date" in (n or "") for n in constraint_names)

    def test_historical_snapshot_repr(self) -> None:
        """__repr__ must include symbol and snapshot_date."""
        snap = HistoricalSnapshot()
        snap.symbol = "BTC"
        snap.snapshot_date = date(2020, 1, 15)
        r = repr(snap)
        assert "BTC" in r
        assert "2020-01-15" in r

    def test_historical_snapshot_categories_is_nullable(self) -> None:
        """categories column must be nullable (not all snapshots have categories)."""
        col = HistoricalSnapshot.__table__.columns["categories"]
        assert col.nullable is True

    def test_historical_snapshot_circulating_supply_is_nullable(self) -> None:
        """circulating_supply column must be nullable."""
        col = HistoricalSnapshot.__table__.columns["circulating_supply"]
        assert col.nullable is True

    def test_historical_snapshot_total_supply_is_nullable(self) -> None:
        """total_supply column must be nullable."""
        col = HistoricalSnapshot.__table__.columns["total_supply"]
        assert col.nullable is True
