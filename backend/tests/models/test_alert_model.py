"""Tests for upgraded Alert ORM model — Phase 11 columns.

Verifies new columns: metadata (JSON), sent_telegram (bool),
acknowledged (bool), acknowledged_at (DateTime), token_symbol (String).
"""

from __future__ import annotations

from app.models.alert import Alert


class TestAlertModelPhase11:
    """Alert model must have Phase 11 columns for full alert pipeline."""

    def test_tablename_is_alerts(self) -> None:
        assert Alert.__tablename__ == "alerts"

    def test_model_has_phase11_columns(self) -> None:
        """Phase 11 adds metadata, sent_telegram, acknowledged, acknowledged_at, token_symbol."""
        columns = {c.name for c in Alert.__table__.columns}
        expected = {
            "id",
            "token_id",
            "alert_type",
            "message",
            "triggered_at",
            "metadata",
            "sent_telegram",
            "acknowledged",
            "acknowledged_at",
            "token_symbol",
        }
        assert expected.issubset(columns)

    def test_create_alert_with_new_columns(self) -> None:
        alert = Alert(
            token_id=1,
            alert_type="listing_candidate",
            message="BTC listing candidate",
            alert_metadata={"listing_score": 85, "signals": ["volume"]},
            sent_telegram=True,
            acknowledged=False,
            token_symbol="BTC",
        )
        assert alert.alert_type == "listing_candidate"
        assert alert.alert_metadata == {"listing_score": 85, "signals": ["volume"]}
        assert alert.sent_telegram is True
        assert alert.acknowledged is False
        assert alert.token_symbol == "BTC"

    def test_default_values(self) -> None:
        """New columns should have sensible defaults at column definition level."""
        cols = {c.name: c for c in Alert.__table__.columns}
        # sent_telegram and acknowledged default to false in the DB
        assert cols["sent_telegram"].server_default is not None
        assert cols["acknowledged"].server_default is not None
        # acknowledged_at and alert_metadata are nullable with no default
        assert cols["acknowledged_at"].nullable is True
        assert cols["metadata"].nullable is True

    def test_token_id_nullable(self) -> None:
        """token_id should accept None for system-wide alerts like DAILY_REPORT."""
        alert = Alert(
            token_id=None,
            alert_type="daily_report",
            message="Daily digest",
            token_symbol=None,
        )
        assert alert.token_id is None
        assert alert.token_symbol is None
