"""TDD tests for GET /rankings/opportunities route."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.market_data import MarketData
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
    *,
    volume_24h: float | None = None,
    market_cap_usd: float | None = None,
) -> tuple[Token, TokenScore, MarketData | None]:
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

    md: MarketData | None = None
    if volume_24h is not None or market_cap_usd is not None:
        md = MarketData()
        md.id = id_
        md.token_id = token_id
        md.price_usd = 1.0
        md.volume_24h_usd = volume_24h
        md.market_cap_usd = market_cap_usd
        md.rank = None
        md.collected_at = datetime(2024, 1, 2, tzinfo=UTC)

    return token, score, md


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

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8, volume_24h=5e9)]
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
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8, volume_24h=5e9),
            _make_score(2, 2, "ETH", "Ethereum", 0.6, 0.6, volume_24h=3e9),
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

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.75, 0.80, volume_24h=5e9)]
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
            _make_score(2, 2, "ETH", "Ethereum", 0.9, 0.9, volume_24h=3e9),
            _make_score(1, 1, "BTC", "Bitcoin", 0.6, 0.6, volume_24h=5e9),
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

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.8, volume_24h=5e9)]
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
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9),
            _make_score(2, 2, "ETH", "Ethereum", 0.7, 0.7, volume_24h=3e9),
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

        rows = [_make_score(1, 42, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9)]
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

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9)]
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

        rows = [_make_score(1, 1, "BTC", "Bitcoin", 0.75, 0.85, volume_24h=5e9)]
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


# ---------------------------------------------------------------------------
# Token filtering — stablecoins, wrapped, dead tokens
# ---------------------------------------------------------------------------


class TestGetRankingsOpportunitiesFiltering:
    """Rankings must exclude stablecoins, wrapped tokens, and dead projects."""

    def test_get_opportunities_excludes_stablecoins(self) -> None:
        """USDT and USDC must never appear in the rankings."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9),
            _make_score(2, 2, "USDT", "Tether", 0.9, 0.95, volume_24h=50e9),
            _make_score(3, 3, "USDC", "USD Coin", 0.85, 0.90, volume_24h=10e9),
            _make_score(4, 4, "ETH", "Ethereum", 0.7, 0.8, volume_24h=3e9),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        symbols = [item["symbol"] for item in data]
        assert "USDT" not in symbols
        assert "USDC" not in symbols
        assert "BTC" in symbols
        assert "ETH" in symbols
        assert len(data) == 2

    def test_get_opportunities_excludes_wrapped_tokens(self) -> None:
        """WBTC, WETH, stETH must be excluded."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "SOL", "Solana", 0.8, 0.85, volume_24h=2e9),
            _make_score(2, 2, "WBTC", "Wrapped Bitcoin", 0.9, 0.92, volume_24h=1e9),
            _make_score(3, 3, "STETH", "Lido Staked ETH", 0.85, 0.88, volume_24h=500e6),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        symbols = [item["symbol"] for item in data]
        assert "WBTC" not in symbols
        assert "STETH" not in symbols
        assert "SOL" in symbols
        assert len(data) == 1

    def test_get_opportunities_excludes_dead_tokens_low_volume(self) -> None:
        """Tokens with volume < $10k should be excluded."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9),
            _make_score(2, 2, "DEADCOIN", "Dead Coin", 0.7, 0.75, volume_24h=100.0),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        symbols = [item["symbol"] for item in data]
        assert "DEADCOIN" not in symbols
        assert "BTC" in symbols
        assert len(data) == 1

    def test_get_opportunities_excludes_none_volume_tokens(self) -> None:
        """Tokens with no volume data are treated as dead."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9),
            _make_score(2, 2, "GHOST", "Ghost Token", 0.7, 0.75),  # No MarketData
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        symbols = [item["symbol"] for item in data]
        assert "GHOST" not in symbols
        assert len(data) == 1

    def test_get_opportunities_ranks_renumbered_after_filtering(self) -> None:
        """After filtering, ranks must be contiguous starting at 1."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "USDT", "Tether", 0.95, 0.99, volume_24h=50e9),
            _make_score(2, 2, "BTC", "Bitcoin", 0.8, 0.9, volume_24h=5e9),
            _make_score(3, 3, "USDC", "USD Coin", 0.85, 0.88, volume_24h=10e9),
            _make_score(4, 4, "ETH", "Ethereum", 0.7, 0.8, volume_24h=3e9),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        ranks = [item["rank"] for item in data]
        assert ranks == [1, 2]
        assert data[0]["symbol"] == "BTC"
        assert data[1]["symbol"] == "ETH"

    def test_get_opportunities_fdusd_and_usd1_excluded(self) -> None:
        """FDUSD and USD1 (the specific stablecoins polluting our ranking) must be excluded."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        rows = [
            _make_score(1, 1, "FDUSD", "First Digital USD", 0.9, 0.95, volume_24h=1e9),
            _make_score(2, 2, "USD1", "USD1 Stablecoin", 0.88, 0.92, volume_24h=500e6),
            _make_score(3, 3, "AVAX", "Avalanche", 0.7, 0.75, volume_24h=800e6),
        ]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        data = response.json()
        symbols = [item["symbol"] for item in data]
        assert "FDUSD" not in symbols
        assert "USD1" not in symbols
        assert symbols == ["AVAX"]
