"""Tests for Phase 14 backtesting API routes — cycle-aware endpoints.

TDD: RED phase — tests written first.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.backtesting import router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/backtesting")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /backtesting/cycles
# ---------------------------------------------------------------------------


class TestGetCycles:
    """Tests for GET /backtesting/cycles."""

    def test_get_cycles_returns_200(self, client: TestClient) -> None:
        response = client.get("/backtesting/cycles")
        assert response.status_code == 200

    def test_get_cycles_returns_list(self, client: TestClient) -> None:
        data = client.get("/backtesting/cycles").json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_get_cycles_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/backtesting/cycles").json()
        first = data[0]
        assert "name" in first
        assert "bottom_date" in first
        assert "top_date" in first
        assert "n_tokens" in first


# ---------------------------------------------------------------------------
# GET /backtesting/weights
# ---------------------------------------------------------------------------


class TestGetWeights:
    """Tests for GET /backtesting/weights — returns current active weights."""

    def test_get_weights_returns_200(self, client: TestClient) -> None:
        response = client.get("/backtesting/weights")
        assert response.status_code == 200

    def test_get_weights_response_has_fields(self, client: TestClient) -> None:
        data = client.get("/backtesting/weights").json()
        assert "fundamental" in data
        assert "growth" in data
        assert "narrative" in data
        assert "listing" in data
        assert "risk" in data
        assert "source" in data

    def test_get_weights_default_source_is_phase9(self, client: TestClient) -> None:
        """Before any calibration, source should be 'default_phase9'."""
        data = client.get("/backtesting/weights").json()
        assert data["source"] == "default_phase9"

    def test_get_weights_sum_to_one(self, client: TestClient) -> None:
        data = client.get("/backtesting/weights").json()
        total = data["fundamental"] + data["growth"] + data["narrative"] + data["listing"] + data["risk"]
        assert total == pytest.approx(1.0, abs=0.01)
