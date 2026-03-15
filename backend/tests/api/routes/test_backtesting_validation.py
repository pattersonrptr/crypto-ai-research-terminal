"""TDD tests for backtesting validation API routes.

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
# POST /backtesting/validate
# ---------------------------------------------------------------------------


class TestPostBacktestingValidate:
    """Tests for POST /backtesting/validate."""

    def test_post_validate_returns_200(self, client: TestClient) -> None:
        """POST /backtesting/validate must return HTTP 200."""
        response = client.post(
            "/backtesting/validate",
            json={"k": 5},
        )
        assert response.status_code == 200

    def test_post_validate_response_has_metrics(self, client: TestClient) -> None:
        """Response must contain precision, recall, hit_rate, token_breakdown."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert "precision_at_k" in body
        assert "recall_at_k" in body
        assert "hit_rate" in body
        assert "token_breakdown" in body
        assert "k" in body

    def test_post_validate_precision_between_0_and_1(self, client: TestClient) -> None:
        """precision_at_k must be in [0, 1]."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert 0.0 <= body["precision_at_k"] <= 1.0

    def test_post_validate_recall_between_0_and_1(self, client: TestClient) -> None:
        """recall_at_k must be in [0, 1]."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert 0.0 <= body["recall_at_k"] <= 1.0

    def test_post_validate_hit_rate_between_0_and_1(self, client: TestClient) -> None:
        """hit_rate must be in [0, 1]."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert 0.0 <= body["hit_rate"] <= 1.0

    def test_post_validate_default_k_is_10(self, client: TestClient) -> None:
        """When k is not provided, default to 10."""
        body = client.post(
            "/backtesting/validate",
            json={},
        ).json()
        assert body["k"] == 10

    def test_post_validate_custom_k(self, client: TestClient) -> None:
        """k must be echoed back from request."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 3},
        ).json()
        assert body["k"] == 3

    def test_post_validate_token_breakdown_is_list(self, client: TestClient) -> None:
        """token_breakdown must be a list."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert isinstance(body["token_breakdown"], list)

    def test_post_validate_model_is_useful_is_bool(self, client: TestClient) -> None:
        """model_is_useful must be a boolean."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert isinstance(body["model_is_useful"], bool)

    def test_post_validate_n_total_tokens_and_n_winners(self, client: TestClient) -> None:
        """Response must include n_total_tokens and n_winners."""
        body = client.post(
            "/backtesting/validate",
            json={"k": 5},
        ).json()
        assert "n_total_tokens" in body
        assert "n_winners" in body
        assert body["n_total_tokens"] >= 0
        assert body["n_winners"] >= 0


# ---------------------------------------------------------------------------
# POST /backtesting/calibrate
# ---------------------------------------------------------------------------


class TestPostBacktestingCalibrate:
    """Tests for POST /backtesting/calibrate."""

    def test_post_calibrate_returns_200(self, client: TestClient) -> None:
        """POST /backtesting/calibrate must return HTTP 200."""
        response = client.post(
            "/backtesting/calibrate",
            json={"step": 0.50},
        )
        assert response.status_code == 200

    def test_post_calibrate_response_has_best_weights(self, client: TestClient) -> None:
        """Response must contain best_weights dict with all 5 pillars."""
        body = client.post(
            "/backtesting/calibrate",
            json={"step": 0.50},
        ).json()
        assert "best_weights" in body
        bw = body["best_weights"]
        assert "fundamental" in bw
        assert "growth" in bw
        assert "narrative" in bw
        assert "listing" in bw
        assert "risk" in bw

    def test_post_calibrate_response_has_precision(self, client: TestClient) -> None:
        """Response must include best_precision_at_k."""
        body = client.post(
            "/backtesting/calibrate",
            json={"step": 0.50},
        ).json()
        assert "best_precision_at_k" in body
        assert isinstance(body["best_precision_at_k"], float)

    def test_post_calibrate_n_combinations(self, client: TestClient) -> None:
        """Response must include n_combinations_tested > 0."""
        body = client.post(
            "/backtesting/calibrate",
            json={"step": 0.50},
        ).json()
        assert body["n_combinations_tested"] > 0
