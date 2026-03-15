"""Tests for GET /tokens/{symbol}/summary — cached AI summaries.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.summaries import router
from app.models.ai_analysis import AiAnalysis
from app.models.token import Token

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> FastAPI:
    """FastAPI app with summaries router mounted."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/tokens")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Test client for the app."""
    return TestClient(app)


def _make_token(symbol: str = "BTC") -> Token:
    """Create a Token stub."""
    t = Token(id=1, symbol=symbol, name="Bitcoin", coingecko_id="bitcoin")
    t.created_at = datetime.now(tz=UTC)
    return t


def _make_cached_analysis() -> AiAnalysis:
    """Create a fresh cached AiAnalysis."""
    a = AiAnalysis(
        id=1,
        token_id=1,
        analysis_type="summary",
        content=(
            '{"summary_text":"Bitcoin is a decentralized digital currency.",'
            '"key_strengths":["decentralized","first-mover"],'
            '"key_risks":["volatility"],'
            '"investment_thesis":"Store of value.",'
            '"target_audience":"Long-term investors"}'
        ),
        model_used="ollama/llama3",
    )
    a.created_at = datetime.now(tz=UTC)
    return a


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetTokenSummary:
    """GET /tokens/{symbol}/summary endpoint tests."""

    @patch("app.api.routes.summaries.get_db")
    def test_summary_returns_cached_when_fresh(
        self, mock_get_db: MagicMock, client: TestClient
    ) -> None:
        """When a fresh cached summary exists, return 200 with content."""
        token = _make_token()
        analysis = _make_cached_analysis()

        mock_session = AsyncMock()
        # First query returns token
        mock_result_token = MagicMock()
        mock_result_token.scalars.return_value.first.return_value = token
        # Second query returns analysis
        mock_result_analysis = MagicMock()
        mock_result_analysis.scalars.return_value.first.return_value = analysis

        mock_session.execute = AsyncMock(side_effect=[mock_result_token, mock_result_analysis])
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        # Override dependency
        from app.api.routes.summaries import router as summaries_router

        app = FastAPI()
        app.include_router(summaries_router, prefix="/tokens")

        from app.db.session import get_db

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        test_client = TestClient(app)

        response = test_client.get("/tokens/BTC/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary_text" in data
        assert data["summary_text"] == "Bitcoin is a decentralized digital currency."

    @patch("app.api.routes.summaries.get_db")
    def test_summary_returns_404_when_token_not_found(
        self, mock_get_db: MagicMock, client: TestClient
    ) -> None:
        """Unknown symbol → 404."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        from app.api.routes.summaries import router as summaries_router

        app = FastAPI()
        app.include_router(summaries_router, prefix="/tokens")

        from app.db.session import get_db

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        test_client = TestClient(app)

        response = test_client.get("/tokens/NONEXISTENT/summary")
        assert response.status_code == 404

    @patch("app.api.routes.summaries.get_db")
    def test_summary_returns_404_when_no_cached_summary(
        self, mock_get_db: MagicMock, client: TestClient
    ) -> None:
        """Token exists but no cached summary → 404 with helpful message."""
        token = _make_token()

        mock_session = AsyncMock()
        mock_result_token = MagicMock()
        mock_result_token.scalars.return_value.first.return_value = token
        mock_result_analysis = MagicMock()
        mock_result_analysis.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[mock_result_token, mock_result_analysis])

        from app.api.routes.summaries import router as summaries_router

        app = FastAPI()
        app.include_router(summaries_router, prefix="/tokens")

        from app.db.session import get_db

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        test_client = TestClient(app)

        response = test_client.get("/tokens/BTC/summary")
        assert response.status_code == 404
        assert "summary" in response.json()["detail"].lower()
