"""TDD tests for GET /tokens and GET /tokens/{symbol} routes."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.score import TokenScore
from app.models.token import Token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(
    id_: int,
    symbol: str,
    name: str,
    coingecko_id: str,
) -> Token:
    """Construct a Token ORM object without a DB session."""
    token = Token()
    token.id = id_
    token.symbol = symbol
    token.name = name
    token.coingecko_id = coingecko_id
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    return token


def _make_score(id_: int, token_id: int, fundamental: float = 0.7, opportunity: float = 0.8) -> TokenScore:
    """Construct a TokenScore ORM object without a DB session."""
    score = TokenScore()
    score.id = id_
    score.token_id = token_id
    score.fundamental_score = fundamental
    score.opportunity_score = opportunity
    score.scored_at = datetime(2024, 1, 2, tzinfo=UTC)
    return score


def _mock_session_rows(rows: Any) -> AsyncMock:
    """Return an AsyncMock session whose execute().all() returns *rows* (for JOIN queries)."""
    result_mock = MagicMock()
    result_mock.all.return_value = rows
    # first() is used by GET /tokens/{symbol}
    result_mock.first.return_value = rows[0] if rows else None

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.execute = AsyncMock(return_value=result_mock)
    return session_mock


# ---------------------------------------------------------------------------
# GET /tokens
# ---------------------------------------------------------------------------


class TestGetTokensList:
    """Tests for GET /tokens."""

    def test_get_tokens_returns_200(self) -> None:
        """GET /tokens must return HTTP 200."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [(_make_token(1, "BTC", "Bitcoin", "bitcoin"), None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_get_tokens_returns_list(self) -> None:
        """GET /tokens must return a JSON array."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [
            (_make_token(1, "BTC", "Bitcoin", "bitcoin"), None),
            (_make_token(2, "ETH", "Ethereum", "ethereum"), None),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_tokens_item_has_required_fields(self) -> None:
        """Each item in GET /tokens must contain id, symbol, name, coingecko_id."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [(_make_token(1, "BTC", "Bitcoin", "bitcoin"), None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert item["id"] == 1
        assert item["symbol"] == "BTC"
        assert item["name"] == "Bitcoin"
        assert item["coingecko_id"] == "bitcoin"

    def test_get_tokens_empty_db_returns_empty_list(self) -> None:
        """GET /tokens must return [] when no tokens exist."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        session = _mock_session_rows([])

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() == []

    def test_get_tokens_item_has_extended_fields(self) -> None:
        """Each item must contain the TokenWithScore extended fields."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [(_make_token(1, "BTC", "Bitcoin", "bitcoin"), None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert "created_at" in item
        assert "latest_score" in item
        assert item["latest_score"] is None  # no score joined
        assert "price_usd" in item
        assert item["price_usd"] is None

    def test_get_tokens_item_with_score_has_latest_score(self) -> None:
        """When a token has a score, latest_score must be populated."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "BTC", "Bitcoin", "bitcoin")
        score = _make_score(10, 1, fundamental=0.75, opportunity=0.85)
        rows = [(token, score)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        item = response.json()[0]
        assert item["latest_score"] is not None
        assert item["latest_score"]["fundamental_score"] == 0.75
        assert item["latest_score"]["opportunity_score"] == 0.85


# ---------------------------------------------------------------------------
# GET /tokens/{symbol}
# ---------------------------------------------------------------------------


class TestGetTokenBySymbol:
    """Tests for GET /tokens/{symbol}."""

    def test_get_token_by_symbol_returns_200(self) -> None:
        """GET /tokens/{symbol} must return 200 when token exists."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [(_make_token(1, "BTC", "Bitcoin", "bitcoin"), None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/BTC")
        app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_get_token_by_symbol_returns_correct_token(self) -> None:
        """GET /tokens/{symbol} must return token data matching the symbol."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        rows = [(_make_token(1, "BTC", "Bitcoin", "bitcoin"), None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/BTC")
        app.dependency_overrides.clear()

        data = response.json()
        assert data["symbol"] == "BTC"
        assert data["name"] == "Bitcoin"
        assert data["coingecko_id"] == "bitcoin"

    def test_get_token_by_symbol_not_found_returns_404(self) -> None:
        """GET /tokens/{symbol} must return 404 when token does not exist."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        session = _mock_session_rows([])

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/UNKNOWN")
        app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_get_token_by_symbol_not_found_returns_detail(self) -> None:
        """GET /tokens/{symbol} 404 response must include a 'detail' field."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        session = _mock_session_rows([])

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/UNKNOWN")
        app.dependency_overrides.clear()

        assert "detail" in response.json()

    def test_get_token_by_symbol_with_score_returns_latest_score(self) -> None:
        """GET /tokens/{symbol} must include latest_score when a score exists."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "ETH", "Ethereum", "ethereum")
        score = _make_score(5, 1, fundamental=0.65, opportunity=0.72)
        rows = [(token, score)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/ETH")
        app.dependency_overrides.clear()

        data = response.json()
        assert data["latest_score"] is not None
        assert data["latest_score"]["fundamental_score"] == 0.65
        assert data["latest_score"]["opportunity_score"] == 0.72
