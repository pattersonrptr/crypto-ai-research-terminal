"""Phase 10 tests for graph route live-data path.

Tests that the graph routes use LiveGraphBuilder when DB data is available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.graph import router
from app.graph.live_graph_builder import LiveGraphBuilder, TokenInfo

if TYPE_CHECKING:
    from app.graph.graph_builder import TokenGraph


@pytest.fixture()
def app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/graph")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _live_graph() -> TokenGraph:
    """Build a small live graph for testing."""
    return LiveGraphBuilder.build(
        [
            TokenInfo("BTC", 800e9, categories=["layer1"], chain="bitcoin"),
            TokenInfo("ETH", 350e9, categories=["layer1"], chain="ethereum"),
            TokenInfo("AAVE", 3.5e9, categories=["defi"], chain="ethereum"),
        ]
    )


class TestGraphLiveDataPath:
    """Verify the routes prefer live data when _build_live_graph succeeds."""

    def test_communities_uses_live_graph_when_available(self, client: TestClient) -> None:
        with patch(
            "app.api.routes.graph._build_live_graph",
            new_callable=AsyncMock,
            return_value=_live_graph(),
        ):
            resp = client.get("/graph/communities")
            assert resp.status_code == 200
            items = resp.json()
            # Live graph has 3 nodes so we should see them
            all_members = [m for item in items for m in item["members"]]
            assert "BTC" in all_members
            assert "ETH" in all_members
            assert "AAVE" in all_members

    def test_centrality_uses_live_graph_when_available(self, client: TestClient) -> None:
        with patch(
            "app.api.routes.graph._build_live_graph",
            new_callable=AsyncMock,
            return_value=_live_graph(),
        ):
            resp = client.get("/graph/centrality?top_n=3")
            assert resp.status_code == 200
            symbols = [item["symbol"] for item in resp.json()]
            assert len(symbols) <= 3

    def test_ecosystem_uses_live_graph_when_available(self, client: TestClient) -> None:
        with patch(
            "app.api.routes.graph._build_live_graph",
            new_callable=AsyncMock,
            return_value=_live_graph(),
        ):
            resp = client.get("/graph/ecosystem")
            assert resp.status_code == 200
            body = resp.json()
            assert body["total_tokens"] == 3

    def test_falls_back_to_seed_when_live_returns_none(self, client: TestClient) -> None:
        with patch(
            "app.api.routes.graph._build_live_graph",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = client.get("/graph/ecosystem")
            assert resp.status_code == 200
            body = resp.json()
            # Seed graph has 15 nodes
            assert body["total_tokens"] == 15
