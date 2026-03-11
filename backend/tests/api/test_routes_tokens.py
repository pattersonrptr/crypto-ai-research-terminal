"""TDD tests for GET /tokens and GET /tokens/{symbol} routes."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
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


def _mock_session(return_value: Any) -> AsyncMock:
    """Return an AsyncMock behaving like AsyncSession returning *return_value* from execute."""
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = return_value
    result_mock.scalar_one_or_none.return_value = return_value

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

        tokens = [_make_token(1, "BTC", "Bitcoin", "bitcoin")]
        session = _mock_session(tokens)

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

        tokens = [
            _make_token(1, "BTC", "Bitcoin", "bitcoin"),
            _make_token(2, "ETH", "Ethereum", "ethereum"),
        ]
        session = _mock_session(tokens)

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

        tokens = [_make_token(1, "BTC", "Bitcoin", "bitcoin")]
        session = _mock_session(tokens)

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

        session = _mock_session([])

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# GET /tokens/{symbol}
# ---------------------------------------------------------------------------

class TestGetTokenBySymbol:
    """Tests for GET /tokens/{symbol}."""

    def test_get_token_by_symbol_returns_200(self) -> None:
        """GET /tokens/{symbol} must return 200 when token exists."""
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "BTC", "Bitcoin", "bitcoin")
        session = _mock_session(token)

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

        token = _make_token(1, "BTC", "Bitcoin", "bitcoin")
        session = _mock_session(token)

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

        session = _mock_session(None)

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

        session = _mock_session(None)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/UNKNOWN")
        app.dependency_overrides.clear()

        assert "detail" in response.json()



