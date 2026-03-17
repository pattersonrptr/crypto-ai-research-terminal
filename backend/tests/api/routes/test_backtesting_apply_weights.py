"""TDD tests for POST /backtesting/apply-weights endpoint.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.backtesting import router

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> FastAPI:
    """FastAPI app with backtesting router mounted."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/backtesting")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /backtesting/apply-weights
# ---------------------------------------------------------------------------


class TestPostApplyWeights:
    """Tests for POST /backtesting/apply-weights."""

    def test_post_apply_weights_returns_200(self, client: TestClient) -> None:
        """POST /backtesting/apply-weights must return HTTP 200."""
        with patch(
            "app.api.routes.backtesting.apply_weights_to_db",
            new_callable=AsyncMock,
            return_value={
                "fundamental": 0.35,
                "growth": 0.20,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
                "source_cycle": "cycle_2_2019_2021",
                "precision_at_k": 0.7,
                "k": 10,
            },
        ):
            response = client.post(
                "/backtesting/apply-weights",
                json={
                    "fundamental": 0.35,
                    "growth": 0.20,
                    "narrative": 0.20,
                    "listing": 0.15,
                    "risk": 0.10,
                },
            )
        assert response.status_code == 200

    def test_post_apply_weights_returns_applied_weights(self, client: TestClient) -> None:
        """Response body must contain the applied weights and metadata."""
        with patch(
            "app.api.routes.backtesting.apply_weights_to_db",
            new_callable=AsyncMock,
            return_value={
                "fundamental": 0.35,
                "growth": 0.20,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
                "source_cycle": "cycle_2_2019_2021",
                "precision_at_k": 0.7,
                "k": 10,
            },
        ):
            body = client.post(
                "/backtesting/apply-weights",
                json={
                    "fundamental": 0.35,
                    "growth": 0.20,
                    "narrative": 0.20,
                    "listing": 0.15,
                    "risk": 0.10,
                },
            ).json()
        assert body["fundamental"] == pytest.approx(0.35)
        assert body["growth"] == pytest.approx(0.20)
        assert body["narrative"] == pytest.approx(0.20)
        assert body["listing"] == pytest.approx(0.15)
        assert body["risk"] == pytest.approx(0.10)
        assert body["source"] == "calibrated"

    def test_post_apply_weights_with_optional_metadata(self, client: TestClient) -> None:
        """Optional source_cycle, precision_at_k, k are persisted."""
        with patch(
            "app.api.routes.backtesting.apply_weights_to_db",
            new_callable=AsyncMock,
            return_value={
                "fundamental": 0.30,
                "growth": 0.25,
                "narrative": 0.20,
                "listing": 0.15,
                "risk": 0.10,
                "source_cycle": "manual",
                "precision_at_k": None,
                "k": None,
            },
        ):
            response = client.post(
                "/backtesting/apply-weights",
                json={
                    "fundamental": 0.30,
                    "growth": 0.25,
                    "narrative": 0.20,
                    "listing": 0.15,
                    "risk": 0.10,
                    "source_cycle": "manual",
                },
            )
        assert response.status_code == 200

    def test_post_apply_weights_validates_sum_to_one(self, client: TestClient) -> None:
        """Weights that do not sum to ~1.0 must be rejected (422)."""
        response = client.post(
            "/backtesting/apply-weights",
            json={
                "fundamental": 0.50,
                "growth": 0.50,
                "narrative": 0.50,
                "listing": 0.50,
                "risk": 0.50,
            },
        )
        assert response.status_code == 422

    def test_post_apply_weights_rejects_negative(self, client: TestClient) -> None:
        """Negative weights must be rejected (422)."""
        response = client.post(
            "/backtesting/apply-weights",
            json={
                "fundamental": -0.10,
                "growth": 0.35,
                "narrative": 0.25,
                "listing": 0.25,
                "risk": 0.25,
            },
        )
        assert response.status_code == 422

    def test_post_apply_weights_rejects_weights_above_one(self, client: TestClient) -> None:
        """Individual weights above 1.0 must be rejected (422)."""
        response = client.post(
            "/backtesting/apply-weights",
            json={
                "fundamental": 1.5,
                "growth": 0.0,
                "narrative": 0.0,
                "listing": 0.0,
                "risk": 0.0,
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /backtesting/weights (updated to read from DB)
# ---------------------------------------------------------------------------


class TestGetWeightsFromDB:
    """Tests for GET /backtesting/weights reading from weight service."""

    def test_get_weights_returns_active_from_service(self, client: TestClient) -> None:
        """GET /weights must read from get_active_weights service."""
        mock_weights = {
            "fundamental": 0.35,
            "growth": 0.20,
            "narrative": 0.20,
            "listing": 0.15,
            "risk": 0.10,
            "source": "calibrated",
        }
        with patch(
            "app.api.routes.backtesting.get_active_weights",
            new_callable=AsyncMock,
            return_value=mock_weights,
        ):
            body = client.get("/backtesting/weights").json()
        assert body["fundamental"] == pytest.approx(0.35)
        assert body["source"] == "calibrated"

    def test_get_weights_returns_defaults_when_no_active(self, client: TestClient) -> None:
        """GET /weights must return defaults when no active weights in DB."""
        mock_weights = {
            "fundamental": 0.30,
            "growth": 0.25,
            "narrative": 0.20,
            "listing": 0.15,
            "risk": 0.10,
            "source": "default_phase9",
        }
        with patch(
            "app.api.routes.backtesting.get_active_weights",
            new_callable=AsyncMock,
            return_value=mock_weights,
        ):
            body = client.get("/backtesting/weights").json()
        assert body["fundamental"] == pytest.approx(0.30)
        assert body["source"] == "default_phase9"
