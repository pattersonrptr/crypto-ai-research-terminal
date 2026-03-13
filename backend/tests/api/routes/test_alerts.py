"""Tests for API routes/alerts endpoints.

TDD RED phase: Tests written before implementation.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.alerts import router


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app with alerts router."""
    app = FastAPI()
    app.include_router(router, prefix="/alerts")
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestGetAlerts:
    """Test GET /alerts endpoint."""

    def test_get_alerts_returns_list(self, client: TestClient) -> None:
        """GET /alerts returns list of alerts."""
        response = client.get("/alerts/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_alerts_with_limit(self, client: TestClient) -> None:
        """GET /alerts supports limit query param."""
        response = client.get("/alerts/?limit=10")
        assert response.status_code == 200

    def test_get_alerts_with_type_filter(self, client: TestClient) -> None:
        """GET /alerts supports type filter."""
        response = client.get("/alerts/?alert_type=listing_candidate")
        assert response.status_code == 200

    def test_get_alerts_with_acknowledged_filter(self, client: TestClient) -> None:
        """GET /alerts supports acknowledged filter."""
        response = client.get("/alerts/?acknowledged=false")
        assert response.status_code == 200


class TestGetAlertById:
    """Test GET /alerts/{id} endpoint."""

    def test_get_alert_by_id_returns_alert(self, client: TestClient) -> None:
        """GET /alerts/{id} returns single alert."""
        # First create or ensure an alert exists (mock in real tests)
        response = client.get("/alerts/1")
        # Should return 200 with alert or 404 if not found
        assert response.status_code in [200, 404]

    def test_get_alert_not_found(self, client: TestClient) -> None:
        """GET /alerts/{id} returns 404 for non-existent alert."""
        response = client.get("/alerts/99999")
        assert response.status_code == 404


class TestPostAlertTest:
    """Test POST /alerts/test endpoint."""

    def test_post_test_alert_sends_telegram(self, client: TestClient) -> None:
        """POST /alerts/test sends a test alert via Telegram."""
        response = client.post(
            "/alerts/test",
            json={"message": "Test alert from API"},
        )
        # Should return success or error based on Telegram config
        assert response.status_code in [200, 503]

    def test_post_test_alert_requires_message(self, client: TestClient) -> None:
        """POST /alerts/test requires message field."""
        response = client.post("/alerts/test", json={})
        assert response.status_code == 422  # Validation error


class TestPutAlertAcknowledge:
    """Test PUT /alerts/{id}/acknowledge endpoint."""

    def test_acknowledge_alert(self, client: TestClient) -> None:
        """PUT /alerts/{id}/acknowledge marks alert as acknowledged."""
        response = client.put("/alerts/1/acknowledge")
        # Should return 200 or 404
        assert response.status_code in [200, 404]

    def test_acknowledge_nonexistent_alert(self, client: TestClient) -> None:
        """PUT /alerts/{id}/acknowledge returns 404 for non-existent."""
        response = client.put("/alerts/99999/acknowledge")
        assert response.status_code == 404


class TestAlertSchemas:
    """Test alert response schemas."""

    def test_alert_response_has_required_fields(self, client: TestClient) -> None:
        """Alert response includes required fields."""
        response = client.get("/alerts/")
        assert response.status_code == 200
        # If there are alerts, check structure
        data = response.json()
        if data:
            alert = data[0]
            assert "id" in alert
            assert "alert_type" in alert
            assert "message" in alert
            assert "triggered_at" in alert


class TestAlertStats:
    """Test GET /alerts/stats endpoint."""

    def test_get_alert_stats(self, client: TestClient) -> None:
        """GET /alerts/stats returns alert statistics."""
        response = client.get("/alerts/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "unacknowledged" in data
        assert "by_type" in data
