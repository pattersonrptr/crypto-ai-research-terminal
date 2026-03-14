"""TDD tests for graph routes.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.graph import router
from app.graph.community_detector import Community
from app.graph.ecosystem_tracker import EcosystemSnapshot

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> FastAPI:
    """FastAPI app with graph router mounted."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/graph")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _make_snapshot() -> EcosystemSnapshot:
    from datetime import UTC, datetime

    return EcosystemSnapshot(
        timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        communities=[
            Community(id=0, members=["BTC", "ETH"]),
            Community(id=1, members=["SOL"]),
        ],
        top_tokens=["BTC", "ETH", "SOL"],
    )


# ---------------------------------------------------------------------------
# GET /graph/communities
# ---------------------------------------------------------------------------


class TestGetGraphCommunities:
    """Tests for GET /graph/communities."""

    def test_get_communities_returns_200(self, client: TestClient) -> None:
        """GET /graph/communities must return HTTP 200."""
        response = client.get("/graph/communities")
        assert response.status_code == 200

    def test_get_communities_returns_list(self, client: TestClient) -> None:
        """Response body must be a JSON list."""
        response = client.get("/graph/communities")
        assert isinstance(response.json(), list)

    def test_get_communities_items_have_required_fields(self, client: TestClient) -> None:
        """Each community item must contain id, members, size."""
        response = client.get("/graph/communities")
        items = response.json()
        assert len(items) > 0
        for item in items:
            assert "id" in item
            assert "members" in item
            assert "size" in item

    def test_get_communities_members_is_list(self, client: TestClient) -> None:
        """members field must be a list of strings."""
        response = client.get("/graph/communities")
        for item in response.json():
            assert isinstance(item["members"], list)

    def test_get_communities_size_matches_members_length(self, client: TestClient) -> None:
        """size must equal len(members)."""
        for item in client.get("/graph/communities").json():
            assert item["size"] == len(item["members"])

    def test_get_communities_uses_detector(self, app: FastAPI) -> None:
        """GET /graph/communities delegates to CommunityDetector.detect()."""
        snapshot = _make_snapshot()
        with patch(
            "app.api.routes.graph.EcosystemTracker.snapshot",
            return_value=snapshot,
        ) as mock_snap:
            c = TestClient(app)
            c.get("/graph/communities")
            mock_snap.assert_called_once()


# ---------------------------------------------------------------------------
# GET /graph/centrality
# ---------------------------------------------------------------------------


class TestGetGraphCentrality:
    """Tests for GET /graph/centrality."""

    def test_get_centrality_returns_200(self, client: TestClient) -> None:
        """GET /graph/centrality must return HTTP 200."""
        response = client.get("/graph/centrality")
        assert response.status_code == 200

    def test_get_centrality_returns_list(self, client: TestClient) -> None:
        """Response body must be a JSON list."""
        response = client.get("/graph/centrality")
        assert isinstance(response.json(), list)

    def test_get_centrality_items_have_required_fields(self, client: TestClient) -> None:
        """Each centrality item must contain symbol, pagerank, betweenness, degree_centrality."""
        response = client.get("/graph/centrality")
        items = response.json()
        assert len(items) > 0
        for item in items:
            assert "symbol" in item
            assert "pagerank" in item
            assert "betweenness" in item
            assert "degree_centrality" in item

    def test_get_centrality_pagerank_is_float(self, client: TestClient) -> None:
        """pagerank must be a float."""
        for item in client.get("/graph/centrality").json():
            assert isinstance(item["pagerank"], float)

    def test_get_centrality_top_n_query_param_limits_results(self, client: TestClient) -> None:
        """?top_n=1 must return at most 1 item."""
        response = client.get("/graph/centrality?top_n=1")
        assert response.status_code == 200
        assert len(response.json()) <= 1

    def test_get_centrality_invalid_top_n_returns_422(self, client: TestClient) -> None:
        """?top_n=0 must return HTTP 422 (validation error)."""
        response = client.get("/graph/centrality?top_n=0")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /graph/ecosystem
# ---------------------------------------------------------------------------


class TestGetGraphEcosystem:
    """Tests for GET /graph/ecosystem."""

    def test_get_ecosystem_returns_200(self, client: TestClient) -> None:
        """GET /graph/ecosystem must return HTTP 200."""
        response = client.get("/graph/ecosystem")
        assert response.status_code == 200

    def test_get_ecosystem_has_required_fields(self, client: TestClient) -> None:
        """Response must contain timestamp, n_communities, total_tokens, top_tokens."""
        body = client.get("/graph/ecosystem").json()
        assert "timestamp" in body
        assert "n_communities" in body
        assert "total_tokens" in body
        assert "top_tokens" in body

    def test_get_ecosystem_top_tokens_is_list(self, client: TestClient) -> None:
        """top_tokens must be a list."""
        body = client.get("/graph/ecosystem").json()
        assert isinstance(body["top_tokens"], list)

    def test_get_ecosystem_n_communities_is_int(self, client: TestClient) -> None:
        """n_communities must be an integer."""
        body = client.get("/graph/ecosystem").json()
        assert isinstance(body["n_communities"], int)
