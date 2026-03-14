"""TDD tests for backtesting routes.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

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
# POST /backtesting/run
# ---------------------------------------------------------------------------


class TestPostBacktestingRun:
    """Tests for POST /backtesting/run."""

    def test_post_run_returns_200(self, client: TestClient) -> None:
        """POST /backtesting/run must return HTTP 200."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "BTC", "cycle": "bull"},
        )
        assert response.status_code == 200

    def test_post_run_response_has_required_fields(self, client: TestClient) -> None:
        """Response body must contain all MetricsReport fields."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "BTC", "cycle": "bull"},
        )
        body = response.json()
        assert "symbol" in body
        assert "cycle" in body
        assert "total_return_pct" in body
        assert "n_trades" in body
        assert "win_rate" in body
        assert "sharpe_ratio" in body
        assert "max_drawdown_pct" in body
        assert "avg_trade_return_pct" in body
        assert "is_profitable" in body

    def test_post_run_returns_correct_symbol(self, client: TestClient) -> None:
        """Response must echo back the requested symbol."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "ETH", "cycle": "bear"},
        )
        assert response.json()["symbol"] == "ETH"

    def test_post_run_returns_correct_cycle(self, client: TestClient) -> None:
        """Response must echo back the requested cycle."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "SOL", "cycle": "accumulation"},
        )
        assert response.json()["cycle"] == "accumulation"

    def test_post_run_total_return_is_float(self, client: TestClient) -> None:
        """total_return_pct must be a float."""
        body = client.post("/backtesting/run", json={"symbol": "BTC", "cycle": "bull"}).json()
        assert isinstance(body["total_return_pct"], float)

    def test_post_run_n_trades_is_non_negative_int(self, client: TestClient) -> None:
        """n_trades must be a non-negative integer."""
        body = client.post("/backtesting/run", json={"symbol": "BTC", "cycle": "bull"}).json()
        assert isinstance(body["n_trades"], int)
        assert body["n_trades"] >= 0

    def test_post_run_win_rate_between_0_and_1(self, client: TestClient) -> None:
        """win_rate must be in [0, 1]."""
        body = client.post("/backtesting/run", json={"symbol": "BTC", "cycle": "bull"}).json()
        assert 0.0 <= body["win_rate"] <= 1.0

    def test_post_run_invalid_cycle_returns_422(self, client: TestClient) -> None:
        """Invalid cycle value must return HTTP 422."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "BTC", "cycle": "superbull"},
        )
        assert response.status_code == 422

    def test_post_run_missing_symbol_returns_422(self, client: TestClient) -> None:
        """Missing symbol field must return HTTP 422."""
        response = client.post(
            "/backtesting/run",
            json={"cycle": "bull"},
        )
        assert response.status_code == 422

    def test_post_run_missing_cycle_returns_422(self, client: TestClient) -> None:
        """Missing cycle field must return HTTP 422."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "BTC"},
        )
        assert response.status_code == 422

    def test_post_run_bear_cycle_returns_200(self, client: TestClient) -> None:
        """POST with cycle=bear must return HTTP 200."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "ETH", "cycle": "bear"},
        )
        assert response.status_code == 200

    def test_post_run_accumulation_cycle_returns_200(self, client: TestClient) -> None:
        """POST with cycle=accumulation must return HTTP 200."""
        response = client.post(
            "/backtesting/run",
            json={"symbol": "SOL", "cycle": "accumulation"},
        )
        assert response.status_code == 200
