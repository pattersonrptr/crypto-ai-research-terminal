"""TDD tests for GET /rankings/opportunities route."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.score import TokenScore
from app.models.token import Token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_score(
    id_: int,
    token_id: int,
    symbol: str,
    name: str,
    fundamental_score: float,
    opportunity_score: float,
) -> tuple[Token, TokenScore, None]:
    """Construct a (Token, TokenScore, MarketData) tuple matching a SQLAlchemy join Row."""
    token = Token()
    token.id = token_id
    token.symbol = symbol
    token.name = name
    token.coingecko_id = symbol.lower()
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)

    score = TokenScore()
    score.id = id_
    score.token_id = token_id
    score.fundamental_score = fundamental_score
    score.opportunity_score = opportunity_score
    score.technology_score = 0.0
    score.tokenomics_score = 0.0
    score.adoption_score = 0.0
    score.dev_activity_score = 0.0
    score.narrative_score = 0.0
    score.growth_score = 0.0
    score.risk_score = 0.0
    score.listing_probability = 0.0
    score.cycle_leader_prob = 0.0
    score.scored_at = datetime(2024, 1, 2, tzinfo=UTC)

    return token, score, None


def _mock_session_rows(rows: Any) -> AsyncMock:
    """Return an AsyncMock session whose execute().all() returns *rows*."""
    result_mock = MagicMock()
    result_mock.all.return_value = rows

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.execute = AsyncMock(return_value=result_mock)
    return session_mock


# ---------------------------------------------------------------------------
# GET /rankings/opportunities
# ---------------------------------------------------------------------------


class TestGetRankingsOpportunities:
    """Tests for GET /rankings/opportunities."""

    def test_get_opportunities_returns_200(self) -> None:
        """GET /rankings/opportunities must return HTTP 200."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_get_opportunities_returns_list(self) -> None:
        """GET /rankings/opportunities must return a JSON array."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8),
            _make_score(2, 2, "ETH", "Ethereum", 0.6, 0.6),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_opportunities_item_has_required_fields(self) -> None:
        """Each ranking item must contain symbol, name, opportunity_score, fundamental_score."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.75, 0.80)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert item["symbol"] == "BTC"
        assert item["name"] == "Bitcoin"
        assert item["opportunity_score"] == pytest.approx(0.80)
        assert item["fundamental_score"] == pytest.approx(0.75)

    def test_get_opportunities_ordered_by_score_descending(self) -> None:
        """GET /rankings/opportunities must return results ordered by opportunity_score DESC."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(2, 2, "ETH", "Ethereum", 0.9, 0.9),
            _make_score(1, 1, "BTC", "Bitcoin", 0.6, 0.6),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        scores = [item["opportunity_score"] for item in data]
        assert scores == sorted(scores, reverse=True)

    def test_get_opportunities_limit_param(self) -> None:
        """GET /rankings/opportunities?limit=1 must return at most 1 result."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?limit=1")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert len(response.json()) <= 1

    def test_get_opportunities_empty_db_returns_empty_list(self) -> None:
        """GET /rankings/opportunities must return [] when no scores exist."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        session = _mock_session_rows([])

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() == []

    def test_get_opportunities_item_has_rank_field(self) -> None:
        """Each ranking item must contain a 'rank' integer starting at 1."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9),
            _make_score(2, 2, "ETH", "Ethereum", 0.7, 0.7),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        assert data[0]["rank"] == 1
        assert data[1]["rank"] == 2

    def test_get_opportunities_item_has_token_nested_object(self) -> None:
        """Each ranking item must contain a 'token' nested object with id, symbol, name."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 42, "BTC", "Bitcoin", 0.8, 0.9)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert "token" in item
        assert item["token"]["id"] == 42
        assert item["token"]["symbol"] == "BTC"
        assert item["token"]["name"] == "Bitcoin"

    def test_get_opportunities_item_has_signals_list(self) -> None:
        """Each ranking item must contain a 'signals' list."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert "signals" in item
        assert isinstance(item["signals"], list)

    def test_get_opportunities_token_has_latest_score(self) -> None:
        """The nested token must expose latest_score with fundamental and opportunity scores."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.75, 0.85)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        token = response.json()[0]["token"]
        assert token["latest_score"] is not None
        assert token["latest_score"]["fundamental_score"] == pytest.approx(0.75)
        assert token["latest_score"]["opportunity_score"] == pytest.approx(0.85)
