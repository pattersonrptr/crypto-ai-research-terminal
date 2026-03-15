"""TDD tests for market cycle route — GET /market/cycle.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.analysis.cycle_detector import CycleIndicators, CyclePhase, CycleResult
from app.api.routes.market import router

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> FastAPI:
    """FastAPI app with market router mounted."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/market")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Test client for the app."""
    return TestClient(app)


def _make_cycle_result(
    phase: CyclePhase = CyclePhase.BULL,
    confidence: float = 0.80,
    fg_index: int = 72,
    fg_label: str = "greed",
    btc_dom: float = 55.0,
    btc_dom_30d: float = 52.0,
    mcap: float = 2.4e12,
    mcap_200d: float | None = 2.0e12,
) -> CycleResult:
    """Helper to build a CycleResult."""
    return CycleResult(
        phase=phase,
        confidence=confidence,
        indicators=CycleIndicators(
            btc_dominance=btc_dom,
            btc_dominance_30d_ago=btc_dom_30d,
            total_market_cap_usd=mcap,
            total_market_cap_200d_ma=mcap_200d,
            fear_greed_index=fg_index,
            fear_greed_label=fg_label,
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetMarketCycle:
    """GET /market/cycle should return the current cycle phase + indicators."""

    def test_get_cycle_returns_200(self, client: TestClient) -> None:
        """Happy path: returns the detected market cycle."""
        result = _make_cycle_result()
        with patch(
            "app.api.routes.market._get_cycle_result",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.get("/market/cycle")

        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == "bull"
        assert data["confidence"] == 0.80

    def test_get_cycle_contains_indicators(self, client: TestClient) -> None:
        """Response must include the indicator details."""
        result = _make_cycle_result()
        with patch(
            "app.api.routes.market._get_cycle_result",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.get("/market/cycle")

        data = response.json()
        indicators = data["indicators"]
        assert indicators["btc_dominance"] == 55.0
        assert indicators["fear_greed_index"] == 72
        assert indicators["fear_greed_label"] == "greed"
        assert indicators["btc_dominance_rising"] is True

    def test_get_cycle_bear_phase(self, client: TestClient) -> None:
        """Verify bear phase is serialised correctly."""
        result = _make_cycle_result(
            phase=CyclePhase.BEAR,
            confidence=0.70,
            fg_index=15,
            fg_label="extreme fear",
        )
        with patch(
            "app.api.routes.market._get_cycle_result",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.get("/market/cycle")

        data = response.json()
        assert data["phase"] == "bear"
        assert data["confidence"] == 0.70

    def test_get_cycle_when_200d_ma_unavailable(self, client: TestClient) -> None:
        """When 200d MA is None, it should serialise as null."""
        result = _make_cycle_result(mcap_200d=None)
        with patch(
            "app.api.routes.market._get_cycle_result",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.get("/market/cycle")

        data = response.json()
        assert data["indicators"]["total_market_cap_200d_ma"] is None
        assert data["indicators"]["market_above_200d_ma"] is None

    def test_get_cycle_response_schema(self, client: TestClient) -> None:
        """Verify response schema completeness."""
        result = _make_cycle_result()
        with patch(
            "app.api.routes.market._get_cycle_result",
            new_callable=AsyncMock,
            return_value=result,
        ):
            response = client.get("/market/cycle")

        data = response.json()
        assert "phase" in data
        assert "confidence" in data
        assert "indicators" in data
        assert "phase_description" in data
        assert isinstance(data["phase_description"], str)
        assert len(data["phase_description"]) > 0
