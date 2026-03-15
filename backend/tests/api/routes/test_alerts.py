"""Tests for API routes/alerts endpoints.

Phase 11: Routes now query PostgreSQL via AsyncSession dependency.
Tests mock the session via dependency_overrides.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.alerts import router
from app.models.alert import Alert

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_APP = FastAPI()
_APP.include_router(router, prefix="/alerts")


def _make_alert(
    *,
    id: int = 1,
    alert_type: str = "listing_candidate",
    message: str = "Test alert",
    token_symbol: str | None = "BTC",
    token_id: int | None = 42,
    sent_telegram: bool = False,
    acknowledged: bool = False,
    triggered_at: datetime | None = None,
) -> Alert:
    """Build a fake Alert ORM instance for tests."""
    a = Alert(
        token_id=token_id,
        alert_type=alert_type,
        message=message,
        token_symbol=token_symbol,
        alert_metadata={"listing_probability": 0.85},
        sent_telegram=sent_telegram,
        acknowledged=acknowledged,
    )
    # Override generated fields that would normally come from DB
    a.id = id  # type: ignore[assignment]
    a.triggered_at = triggered_at or datetime.now(UTC)  # type: ignore[assignment]
    return a


def _mock_session_for_list(alerts: list[Alert]) -> AsyncMock:
    """Return a mocked AsyncSession whose execute returns given alerts."""
    session = AsyncMock(spec=AsyncSession)
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = alerts
    scalars_mock.first.return_value = alerts[0] if alerts else None
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    session.execute = AsyncMock(return_value=result_mock)
    return session


def _mock_session_for_stats(
    total: int,
    unacknowledged: int,
    by_type: list[tuple[str, int]],
) -> AsyncMock:
    """Return a mocked AsyncSession for the /stats endpoint."""
    session = AsyncMock(spec=AsyncSession)
    call_count = 0

    async def _fake_execute(stmt: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalar_one.return_value = total
        elif call_count == 2:
            result.scalar_one.return_value = unacknowledged
        else:
            result.all.return_value = by_type
        return result

    session.execute = _fake_execute  # type: ignore[assignment]
    return session


def _get_client(session: AsyncMock) -> TestClient:
    """Build a TestClient with the session override applied."""
    from app.db.session import get_db  # noqa: PLC0415

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield session  # type: ignore[arg-type]

    _APP.dependency_overrides[get_db] = _override
    return TestClient(_APP)


@pytest.fixture(autouse=True)
def _cleanup_overrides() -> Generator[None, None, None]:  # noqa: PT004
    """Clear dependency overrides after each test."""
    yield
    _APP.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------


class TestGetAlerts:
    """Test GET /alerts endpoint."""

    def test_get_alerts_returns_list(self) -> None:
        """GET /alerts returns list of alerts."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.get("/alerts/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_alerts_with_limit(self) -> None:
        """GET /alerts supports limit query param."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.get("/alerts/?limit=10")
        assert response.status_code == 200

    def test_get_alerts_with_type_filter(self) -> None:
        """GET /alerts supports type filter."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.get("/alerts/?alert_type=listing_candidate")
        assert response.status_code == 200

    def test_get_alerts_with_acknowledged_filter(self) -> None:
        """GET /alerts supports acknowledged filter."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.get("/alerts/?acknowledged=false")
        assert response.status_code == 200

    def test_get_alerts_returns_correct_shape(self) -> None:
        """Response items must include Phase 11 fields."""
        alert = _make_alert()
        session = _mock_session_for_list([alert])
        client = _get_client(session)
        response = client.get("/alerts/")
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert "id" in item
        assert "alert_type" in item
        assert "message" in item
        assert "metadata" in item
        assert "sent_telegram" in item
        assert "acknowledged" in item
        assert "created_at" in item


class TestGetAlertById:
    """Test GET /alerts/{id} endpoint."""

    def test_get_alert_by_id_returns_alert(self) -> None:
        """GET /alerts/{id} returns single alert."""
        alert = _make_alert(id=1)
        session = _mock_session_for_list([alert])
        client = _get_client(session)
        response = client.get("/alerts/1")
        assert response.status_code == 200

    def test_get_alert_not_found(self) -> None:
        """GET /alerts/{id} returns 404 for non-existent alert."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.get("/alerts/99999")
        assert response.status_code == 404


class TestPostAlertTest:
    """Test POST /alerts/test endpoint."""

    def test_post_test_alert_requires_message(self) -> None:
        """POST /alerts/test requires message field."""
        # Test alert does not need DB session, but app needs dependency anyway.
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.post("/alerts/test", json={})
        assert response.status_code == 422

    def test_post_test_alert_no_telegram(self) -> None:
        """POST /alerts/test returns 503 when Telegram is not configured."""
        from unittest.mock import patch  # noqa: PLC0415

        session = _mock_session_for_list([])
        client = _get_client(session)
        with patch("app.api.routes.alerts.settings") as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_chat_id = ""
            response = client.post("/alerts/test", json={"message": "hi"})
        assert response.status_code == 503


class TestPutAlertAcknowledge:
    """Test PUT /alerts/{id}/acknowledge endpoint."""

    def test_acknowledge_nonexistent_alert(self) -> None:
        """PUT /alerts/{id}/acknowledge returns 404 for non-existent."""
        session = _mock_session_for_list([])
        client = _get_client(session)
        response = client.put("/alerts/99999/acknowledge")
        assert response.status_code == 404

    def test_acknowledge_alert_returns_200(self) -> None:
        """PUT /alerts/{id}/acknowledge returns 200 for existing alert."""
        alert = _make_alert(id=1)
        session = _mock_session_for_list([alert])
        session.commit = AsyncMock()
        client = _get_client(session)
        response = client.put("/alerts/1/acknowledge")
        assert response.status_code == 200
        body = response.json()
        assert body["acknowledged"] is True


class TestAlertStats:
    """Test GET /alerts/stats endpoint."""

    def test_get_alert_stats(self) -> None:
        """GET /alerts/stats returns alert statistics."""
        session = _mock_session_for_stats(
            total=5,
            unacknowledged=3,
            by_type=[("listing_candidate", 3), ("rugpull_risk", 2)],
        )
        client = _get_client(session)
        response = client.get("/alerts/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["unacknowledged"] == 3
        assert "listing_candidate" in data["by_type"]
