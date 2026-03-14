"""TDD tests for Phase 9 API — all 11 sub-scores + market data in responses.

Tests that GET /tokens/{symbol} and GET /tokens/ map all sub-scores
from the TokenScore model and include market data from MarketData join.
"""

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


def _make_token(id_: int, symbol: str, name: str, coingecko_id: str) -> Token:
    token = Token()
    token.id = id_
    token.symbol = symbol
    token.name = name
    token.coingecko_id = coingecko_id
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    return token


def _make_full_score(id_: int, token_id: int) -> TokenScore:
    """Construct a TokenScore with all 11 sub-scores populated."""
    score = TokenScore()
    score.id = id_
    score.token_id = token_id
    score.fundamental_score = 0.75
    score.opportunity_score = 0.82
    score.technology_score = 0.65
    score.tokenomics_score = 0.70
    score.adoption_score = 0.80
    score.dev_activity_score = 0.55
    score.narrative_score = 0.60
    score.growth_score = 0.50
    score.risk_score = 0.85
    score.listing_probability = 0.90
    score.cycle_leader_prob = 0.40
    score.scored_at = datetime(2024, 1, 2, tzinfo=UTC)
    return score


def _make_market_data(id_: int, token_id: int) -> MarketData:
    """Construct a MarketData snapshot."""
    md = MarketData()
    md.id = id_
    md.token_id = token_id
    md.price_usd = 3500.0
    md.market_cap_usd = 420_000_000_000.0
    md.volume_24h_usd = 15_000_000_000.0
    md.rank = 2
    md.ath_usd = 4800.0
    md.circulating_supply = 120_000_000.0
    md.collected_at = datetime(2024, 1, 2, tzinfo=UTC)
    return md


def _mock_session_rows(rows: Any) -> AsyncMock:
    result_mock = MagicMock()
    result_mock.all.return_value = rows
    result_mock.first.return_value = rows[0] if rows else None

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.execute = AsyncMock(return_value=result_mock)
    return session_mock


class TestTokensRoutePhase9SubScores:
    """GET /tokens/{symbol} must return all 11 sub-scores."""

    def test_token_detail_returns_all_sub_scores(self) -> None:
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "ETH", "Ethereum", "ethereum")
        score = _make_full_score(10, 1)
        md = _make_market_data(100, 1)
        rows = [(token, score, md)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/ETH")
        app.dependency_overrides.clear()

        data = response.json()
        ls = data["latest_score"]
        assert ls is not None
        assert ls["fundamental_score"] == pytest.approx(0.75)
        assert ls["opportunity_score"] == pytest.approx(0.82)
        assert ls["technology_score"] == pytest.approx(0.65)
        assert ls["tokenomics_score"] == pytest.approx(0.70)
        assert ls["adoption_score"] == pytest.approx(0.80)
        assert ls["dev_activity_score"] == pytest.approx(0.55)
        assert ls["narrative_score"] == pytest.approx(0.60)
        assert ls["growth_score"] == pytest.approx(0.50)
        assert ls["risk_score"] == pytest.approx(0.85)
        assert ls["listing_probability"] == pytest.approx(0.90)
        assert ls["cycle_leader_prob"] == pytest.approx(0.40)


class TestTokensRoutePhase9MarketData:
    """GET /tokens/{symbol} must return market data from MarketData join."""

    def test_token_detail_returns_market_data(self) -> None:
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "ETH", "Ethereum", "ethereum")
        score = _make_full_score(10, 1)
        md = _make_market_data(100, 1)
        rows = [(token, score, md)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/ETH")
        app.dependency_overrides.clear()

        data = response.json()
        assert data["price_usd"] == pytest.approx(3500.0)
        assert data["market_cap"] == pytest.approx(420_000_000_000.0)
        assert data["volume_24h"] == pytest.approx(15_000_000_000.0)
        assert data["rank"] == 2

    def test_token_detail_no_market_data_returns_nulls(self) -> None:
        from app.api.routes.tokens import get_db  # noqa: PLC0415

        token = _make_token(1, "ETH", "Ethereum", "ethereum")
        score = _make_full_score(10, 1)
        rows = [(token, score, None)]
        session = _mock_session_rows(rows)

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/tokens/ETH")
        app.dependency_overrides.clear()

        data = response.json()
        assert data["price_usd"] is None
        assert data["market_cap"] is None
