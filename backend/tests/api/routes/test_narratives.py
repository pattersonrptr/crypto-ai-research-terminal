"""Tests for API routes/narratives endpoints.

TDD RED phase: tests written before implementation.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.narratives import router


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app with narratives router."""
    app = FastAPI()
    app.include_router(router, prefix="/narratives")
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestGetNarratives:
    """Test GET /narratives endpoint."""

    def test_get_narratives_returns_200(self, client: TestClient) -> None:
        """GET /narratives should return HTTP 200."""
        response = client.get("/narratives/")
        assert response.status_code == 200

    def test_get_narratives_returns_list(self, client: TestClient) -> None:
        """GET /narratives should return a JSON list."""
        response = client.get("/narratives/")
        assert isinstance(response.json(), list)

    def test_get_narratives_items_have_required_fields(self, client: TestClient) -> None:
        """Each narrative item should contain required schema fields."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "momentum_score" in item
            assert "trend" in item
            assert "tokens" in item
            assert "keywords" in item
            assert "token_count" in item

    def test_get_narratives_tokens_is_list(self, client: TestClient) -> None:
        """tokens field should be a list of strings."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["tokens"], list)

    def test_get_narratives_keywords_is_list(self, client: TestClient) -> None:
        """keywords field should be a list of strings."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["keywords"], list)

    def test_get_narratives_momentum_score_is_float(self, client: TestClient) -> None:
        """momentum_score field should be a number."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["momentum_score"], int | float)

    def test_get_narratives_trend_is_valid_string(self, client: TestClient) -> None:
        """trend field should be one of the valid trend values."""
        valid_trends = {"accelerating", "stable", "declining"}
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert item["trend"] in valid_trends

    def test_get_narratives_token_count_matches_tokens_length(self, client: TestClient) -> None:
        """token_count should equal len(tokens)."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert item["token_count"] == len(item["tokens"])

    def test_get_narratives_returns_nonempty_list(self, client: TestClient) -> None:
        """GET /narratives should return at least one narrative."""
        response = client.get("/narratives/")
        items = response.json()
        assert len(items) >= 1

    def test_get_narratives_id_is_integer(self, client: TestClient) -> None:
        """id field should be a positive integer."""
        response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["id"], int)
            assert item["id"] > 0
