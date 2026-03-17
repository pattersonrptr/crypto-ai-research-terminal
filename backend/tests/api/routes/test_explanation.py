"""TDD tests for GET /tokens/{symbol}/explanation endpoint.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.tokens import router
from app.db.session import get_db

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_token(symbol: str = "ETH", name: str = "Ethereum") -> MagicMock:
    token = MagicMock()
    token.id = 1
    token.symbol = symbol
    token.name = name
    token.coingecko_id = "ethereum"
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    return token


def _make_score() -> MagicMock:
    score = MagicMock()
    score.fundamental_score = 0.75
    score.technology_score = 0.80
    score.tokenomics_score = 0.70
    score.adoption_score = 0.65
    score.dev_activity_score = 0.85
    score.narrative_score = 0.60
    score.growth_score = 0.70
    score.risk_score = 0.50
    score.listing_probability = 0.30
    score.cycle_leader_prob = 0.10
    score.opportunity_score = 0.68
    score.scored_at = datetime(2024, 1, 1, tzinfo=UTC)
    return score


def _make_market_data() -> MagicMock:
    md = MagicMock()
    md.price_usd = 3500.0
    md.market_cap_usd = 420_000_000_000
    md.volume_24h_usd = 15_000_000_000
    md.price_change_7d = 5.2
    md.rank = 2
    return md


def _make_social_data() -> MagicMock:
    sd = MagicMock()
    sd.reddit_subscribers = 1_500_000
    sd.reddit_posts_24h = 120
    sd.sentiment_score = 0.7
    sd.twitter_mentions_24h = 5000
    sd.twitter_engagement = 25000
    return sd


@pytest.fixture()
def app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router, prefix="/tokens")
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /tokens/{symbol}/explanation
# ---------------------------------------------------------------------------


class TestGetTokenExplanation:
    """Tests for GET /tokens/{symbol}/explanation."""

    def test_get_explanation_returns_200(self, client: TestClient) -> None:
        """GET /tokens/ETH/explanation must return HTTP 200."""
        mock_result = MagicMock()
        mock_result.first.return_value = (
            _make_token(),
            _make_score(),
            _make_market_data(),
            _make_social_data(),
        )
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=mock_result.first.return_value,
        ):
            response = client.get("/tokens/ETH/explanation")
        assert response.status_code == 200

    def test_get_explanation_returns_pillars(self, client: TestClient) -> None:
        """Response must include pillar explanations."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=(
                _make_token(),
                _make_score(),
                _make_market_data(),
                _make_social_data(),
            ),
        ):
            response = client.get("/tokens/ETH/explanation")
        data = response.json()
        assert "explanations" in data
        assert len(data["explanations"]) == 6  # 5 pillars + overall

    def test_get_explanation_each_pillar_has_required_fields(self, client: TestClient) -> None:
        """Each explanation must have pillar, score, explanation."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=(
                _make_token(),
                _make_score(),
                _make_market_data(),
                _make_social_data(),
            ),
        ):
            response = client.get("/tokens/ETH/explanation")
        data = response.json()
        for item in data["explanations"]:
            assert "pillar" in item
            assert "score" in item
            assert "explanation" in item

    def test_get_explanation_includes_symbol(self, client: TestClient) -> None:
        """Response must include the token symbol."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=(
                _make_token(),
                _make_score(),
                _make_market_data(),
                _make_social_data(),
            ),
        ):
            response = client.get("/tokens/ETH/explanation")
        data = response.json()
        assert data["symbol"] == "ETH"

    def test_get_explanation_404_unknown_symbol(self, client: TestClient) -> None:
        """GET /tokens/UNKNOWN/explanation must return 404 for unknown tokens."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get("/tokens/UNKNOWN/explanation")
        assert response.status_code == 404

    def test_get_explanation_404_no_score(self, client: TestClient) -> None:
        """GET /tokens/ETH/explanation must return 404 when token has no scores."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=(_make_token(), None, _make_market_data(), None),
        ):
            response = client.get("/tokens/ETH/explanation")
        assert response.status_code == 404

    def test_get_explanation_works_without_social_data(self, client: TestClient) -> None:
        """Explanation must work even when social data is None."""
        with patch(
            "app.api.routes.tokens._fetch_token_with_details",
            new_callable=AsyncMock,
            return_value=(
                _make_token(),
                _make_score(),
                _make_market_data(),
                None,
            ),
        ):
            response = client.get("/tokens/ETH/explanation")
        assert response.status_code == 200
        data = response.json()
        assert len(data["explanations"]) == 6
