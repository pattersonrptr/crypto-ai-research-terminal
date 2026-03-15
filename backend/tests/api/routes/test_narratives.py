"""Tests for API routes/narratives endpoints.

TDD RED phase: tests written before implementation.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.narratives import router

_FAKE_LIVE_NARRATIVES = [
    {
        "id": 1,
        "name": "AI & ML",
        "momentum_score": 9.2,
        "trend": "accelerating",
        "tokens": ["FET", "RNDR"],
        "keywords": ["AI", "compute"],
        "token_count": 2,
    },
    {
        "id": 2,
        "name": "DeFi Lending",
        "momentum_score": 6.4,
        "trend": "stable",
        "tokens": ["AAVE", "COMP"],
        "keywords": ["yield", "lending"],
        "token_count": 2,
    },
]


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


def _patch_live(data: list[dict]) -> AsyncMock:  # type: ignore[type-arg]
    """Return a patcher that makes fetch_latest_narratives return *data*."""
    return patch(
        "app.api.routes.narratives.fetch_latest_narratives",
        new_callable=AsyncMock,
        return_value=data,
    )


class TestGetNarratives:
    """Test GET /narratives endpoint with live data."""

    def test_get_narratives_returns_200(self, client: TestClient) -> None:
        """GET /narratives should return HTTP 200."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        assert response.status_code == 200

    def test_get_narratives_returns_list(self, client: TestClient) -> None:
        """GET /narratives should return a JSON list."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        assert isinstance(response.json(), list)

    def test_get_narratives_items_have_required_fields(self, client: TestClient) -> None:
        """Each narrative item should contain required schema fields."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
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
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["tokens"], list)

    def test_get_narratives_keywords_is_list(self, client: TestClient) -> None:
        """keywords field should be a list of strings."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["keywords"], list)

    def test_get_narratives_momentum_score_is_float(self, client: TestClient) -> None:
        """momentum_score field should be a number."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["momentum_score"], int | float)

    def test_get_narratives_trend_is_valid_string(self, client: TestClient) -> None:
        """trend field should be one of the valid trend values."""
        valid_trends = {"accelerating", "stable", "declining"}
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert item["trend"] in valid_trends

    def test_get_narratives_token_count_matches_tokens_length(self, client: TestClient) -> None:
        """token_count should equal len(tokens)."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert item["token_count"] == len(item["tokens"])

    def test_get_narratives_returns_nonempty_list(self, client: TestClient) -> None:
        """GET /narratives with live data should return at least one narrative."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        assert len(items) >= 1

    def test_get_narratives_id_is_integer(self, client: TestClient) -> None:
        """id field should be a positive integer."""
        with _patch_live(_FAKE_LIVE_NARRATIVES):
            response = client.get("/narratives/")
        items = response.json()
        for item in items:
            assert isinstance(item["id"], int)
            assert item["id"] > 0


class TestGetNarrativesLiveData:
    """GET /narratives returns live DB data when available, empty list otherwise."""

    @pytest.mark.asyncio
    async def test_get_narratives_uses_live_data_when_db_returns_narratives(
        self,
    ) -> None:
        """When fetch_latest_narratives returns data the endpoint must use it."""
        from httpx import AsyncClient  # noqa: PLC0415

        from app.main import app as main_app  # noqa: PLC0415

        live_narratives = [
            {
                "id": 99,
                "name": "Live Narrative",
                "momentum_score": 9.5,
                "trend": "accelerating",
                "tokens": ["XYZ", "ABC"],
                "keywords": ["live", "test"],
                "token_count": 2,
            }
        ]
        with patch(
            "app.api.routes.narratives.fetch_latest_narratives",
            new_callable=AsyncMock,
            return_value=live_narratives,
        ):
            async with AsyncClient(app=main_app, base_url="http://test") as client:
                response = await client.get("/narratives/")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Live Narrative"

    @pytest.mark.asyncio
    async def test_get_narratives_returns_empty_list_when_db_has_no_data(
        self,
    ) -> None:
        """When fetch_latest_narratives returns empty list the endpoint returns []."""
        from httpx import AsyncClient  # noqa: PLC0415

        from app.main import app as main_app  # noqa: PLC0415

        with patch(
            "app.api.routes.narratives.fetch_latest_narratives",
            new_callable=AsyncMock,
            return_value=[],
        ):
            async with AsyncClient(app=main_app, base_url="http://test") as client:
                response = await client.get("/narratives/")
        assert response.status_code == 200
        data = response.json()
        assert data == []
