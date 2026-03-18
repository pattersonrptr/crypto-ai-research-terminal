"""TDD tests for server-side filtering, sorting, pagination, and search on rankings API.

Phase 15: These tests validate that query params (categories, exclude_categories,
sort, order, search, page, page_size) are applied server-side (in SQL) rather
than post-query. They use a real SQLite in-memory database instead of mocks.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from tests.conftest_helpers import create_sqlite_tables

# ---------------------------------------------------------------------------
# Fixtures: real async SQLite DB
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite engine with all ORM tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(create_sqlite_tables)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):  # type: ignore[return]
    """Yield an async session bound to the test engine."""
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def _seed_token(
    session: AsyncSession,
    *,
    symbol: str,
    name: str,
    coingecko_id: str | None = None,
    category: str | None = None,
    opportunity_score: float = 0.5,
    fundamental_score: float = 0.5,
    volume_24h: float = 1e9,
    market_cap: float = 1e9,
    price_usd: float = 1.0,
) -> Token:
    """Insert a token + score + market_data row and return the Token."""
    token = Token()
    token.symbol = symbol
    token.name = name
    token.coingecko_id = coingecko_id or symbol.lower()
    token.category = category
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    session.add(token)
    await session.flush()

    score = TokenScore()
    score.token_id = token.id
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
    session.add(score)

    md = MarketData()
    md.token_id = token.id
    md.price_usd = price_usd
    md.volume_24h_usd = volume_24h
    md.market_cap_usd = market_cap
    md.rank = None
    md.collected_at = datetime(2024, 1, 2, tzinfo=UTC)
    session.add(md)

    await session.flush()
    return token


# ---------------------------------------------------------------------------
# Paginated response shape
# ---------------------------------------------------------------------------


class TestPaginatedResponseShape:
    """The response must include data + total_count for pagination UI."""

    async def test_response_has_data_and_total_count(self, async_session: AsyncSession) -> None:
        """Response body must have 'data' (list) and 'total_count' (int) keys."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "total_count" in body
        assert isinstance(body["data"], list)
        assert isinstance(body["total_count"], int)

    async def test_total_count_reflects_unfiltered_total(self, async_session: AsyncSession) -> None:
        """total_count must reflect the count after category filtering, before pagination."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="ETH", name="Ethereum", category="l1")
        await _seed_token(async_session, symbol="SOL", name="Solana", category="l1")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?page=1&page_size=2")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 3
        assert len(body["data"]) == 2


# ---------------------------------------------------------------------------
# Category filtering
# ---------------------------------------------------------------------------


class TestCategoryFiltering:
    """Test category include/exclude query params."""

    async def test_categories_include_filter(self, async_session: AsyncSession) -> None:
        """?categories=l1 must return only tokens with category='l1'."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="UNI", name="Uniswap", category="defi")
        await _seed_token(async_session, symbol="SOL", name="Solana", category="l1")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?categories=l1")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert "BTC" in symbols
        assert "SOL" in symbols
        assert "UNI" not in symbols
        assert body["total_count"] == 2

    async def test_categories_include_multiple(self, async_session: AsyncSession) -> None:
        """?categories=l1,defi must return tokens from both categories."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="UNI", name="Uniswap", category="defi")
        await _seed_token(async_session, symbol="DOGE", name="Dogecoin", category="memecoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?categories=l1,defi")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert "BTC" in symbols
        assert "UNI" in symbols
        assert "DOGE" not in symbols
        assert body["total_count"] == 2

    async def test_categories_empty_returns_all(self, async_session: AsyncSession) -> None:
        """Empty categories param must return all tokens (no category filter)."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="UNI", name="Uniswap", category="defi")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 2

    async def test_exclude_categories_filter(self, async_session: AsyncSession) -> None:
        """?exclude_categories=stablecoin must exclude tokens with that category."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="USDT", name="Tether", category="stablecoin")
        await _seed_token(async_session, symbol="USDC", name="USD Coin", category="stablecoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?exclude_categories=stablecoin")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert "BTC" in symbols
        assert "USDT" not in symbols
        assert "USDC" not in symbols
        assert body["total_count"] == 1

    async def test_exclude_categories_multiple(self, async_session: AsyncSession) -> None:
        """?exclude_categories=stablecoin,wrapped must exclude both."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="USDT", name="Tether", category="stablecoin")
        await _seed_token(async_session, symbol="WBTC", name="Wrapped Bitcoin", category="wrapped")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?exclude_categories=stablecoin,wrapped")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert symbols == ["BTC"]
        assert body["total_count"] == 1

    async def test_include_and_exclude_combined(self, async_session: AsyncSession) -> None:
        """Include + exclude: exclude is applied after include."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="ETH", name="Ethereum", category="l1")
        await _seed_token(async_session, symbol="UNI", name="Uniswap", category="defi")
        await _seed_token(async_session, symbol="DOGE", name="Dogecoin", category="memecoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        # Include l1 + defi, but then exclude defi → only l1
        response = client.get("/rankings/opportunities?categories=l1,defi&exclude_categories=defi")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert "BTC" in symbols
        assert "ETH" in symbols
        assert "UNI" not in symbols
        assert "DOGE" not in symbols
        assert body["total_count"] == 2

    async def test_null_category_included_when_no_filter(self, async_session: AsyncSession) -> None:
        """Tokens with null category must still appear when no category filter is set."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="NEW", name="NewToken", category=None)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 2


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


class TestServerSideSorting:
    """Test sort + order query params."""

    async def test_default_sort_by_opportunity_score_desc(
        self, async_session: AsyncSession
    ) -> None:
        """Default sort must be opportunity_score descending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="LOW", name="Low Score", opportunity_score=0.3)
        await _seed_token(async_session, symbol="HIGH", name="High Score", opportunity_score=0.9)
        await _seed_token(async_session, symbol="MID", name="Mid Score", opportunity_score=0.6)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert symbols == ["HIGH", "MID", "LOW"]

    async def test_sort_by_name_asc(self, async_session: AsyncSession) -> None:
        """?sort=name&order=asc must sort alphabetically ascending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="SOL", name="Solana")
        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await _seed_token(async_session, symbol="ETH", name="Ethereum")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?sort=name&order=asc")
        app.dependency_overrides.clear()

        body = response.json()
        names = [item["name"] for item in body["data"]]
        assert names == ["Bitcoin", "Ethereum", "Solana"]

    async def test_sort_by_market_cap_desc(self, async_session: AsyncSession) -> None:
        """?sort=market_cap&order=desc must sort by market cap descending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="SMALL", name="Small Cap", market_cap=1e6)
        await _seed_token(async_session, symbol="BIG", name="Big Cap", market_cap=1e12)
        await _seed_token(async_session, symbol="MID", name="Mid Cap", market_cap=1e9)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?sort=market_cap&order=desc")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert symbols == ["BIG", "MID", "SMALL"]

    async def test_sort_by_volume_24h_asc(self, async_session: AsyncSession) -> None:
        """?sort=volume_24h&order=asc must sort by volume ascending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="HIGH", name="High Vol", volume_24h=5e9)
        await _seed_token(async_session, symbol="LOW", name="Low Vol", volume_24h=1e6)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?sort=volume_24h&order=asc")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert symbols == ["LOW", "HIGH"]

    async def test_sort_by_fundamental_score(self, async_session: AsyncSession) -> None:
        """?sort=fundamental_score&order=desc must sort by fundamental score descending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="A", name="Alpha", fundamental_score=0.9)
        await _seed_token(async_session, symbol="B", name="Beta", fundamental_score=0.3)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?sort=fundamental_score&order=desc")
        app.dependency_overrides.clear()

        body = response.json()
        symbols = [item["symbol"] for item in body["data"]]
        assert symbols == ["A", "B"]

    async def test_invalid_sort_column_returns_422(self, async_session: AsyncSession) -> None:
        """An invalid sort column must return 422 validation error."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?sort=nonexistent")
        app.dependency_overrides.clear()

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestServerSideSearch:
    """Test search query param (ILIKE on symbol and name)."""

    async def test_search_by_symbol(self, async_session: AsyncSession) -> None:
        """?search=btc must return tokens whose symbol matches (case-insensitive)."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await _seed_token(async_session, symbol="ETH", name="Ethereum")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?search=btc")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 1
        assert body["data"][0]["symbol"] == "BTC"

    async def test_search_by_name(self, async_session: AsyncSession) -> None:
        """?search=ethe must match 'Ethereum' by name."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await _seed_token(async_session, symbol="ETH", name="Ethereum")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?search=ethe")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 1
        assert body["data"][0]["symbol"] == "ETH"

    async def test_search_case_insensitive(self, async_session: AsyncSession) -> None:
        """Search must be case-insensitive."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="SOL", name="Solana")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?search=SOLANA")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 1

    async def test_search_no_match_returns_empty(self, async_session: AsyncSession) -> None:
        """Search with no match must return empty data and total_count=0."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?search=xyz")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 0
        assert body["data"] == []

    async def test_search_combined_with_category_filter(self, async_session: AsyncSession) -> None:
        """Search + category filter must both apply."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="BSV", name="Bitcoin SV", category="fork")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?search=bitcoin&categories=l1")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["total_count"] == 1
        assert body["data"][0]["symbol"] == "BTC"


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestServerSidePagination:
    """Test page + page_size query params."""

    async def test_default_pagination_page_1_size_50(self, async_session: AsyncSession) -> None:
        """Default page=1, page_size=50 must return at most 50 items."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        # Seed 3 tokens — all should be returned with default page size
        for i in range(3):
            await _seed_token(
                async_session,
                symbol=f"T{i}",
                name=f"Token {i}",
                coingecko_id=f"token-{i}",
            )
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities")
        app.dependency_overrides.clear()

        body = response.json()
        assert len(body["data"]) == 3
        assert body["total_count"] == 3

    async def test_page_size_limits_results(self, async_session: AsyncSession) -> None:
        """?page_size=2 must return at most 2 items per page."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        for i in range(5):
            await _seed_token(
                async_session,
                symbol=f"T{i}",
                name=f"Token {i}",
                coingecko_id=f"token-{i}",
            )
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?page_size=2")
        app.dependency_overrides.clear()

        body = response.json()
        assert len(body["data"]) == 2
        assert body["total_count"] == 5

    async def test_page_2_returns_next_items(self, async_session: AsyncSession) -> None:
        """?page=2&page_size=2 must skip the first 2 and return the next 2."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        # Create tokens with descending opportunity scores so order is deterministic
        for i in range(5):
            await _seed_token(
                async_session,
                symbol=f"T{i}",
                name=f"Token {i}",
                coingecko_id=f"token-{i}",
                opportunity_score=0.9 - (i * 0.1),
            )
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)

        # Page 1
        resp1 = client.get("/rankings/opportunities?page=1&page_size=2")
        body1 = resp1.json()

        # Page 2
        resp2 = client.get("/rankings/opportunities?page=2&page_size=2")
        body2 = resp2.json()
        app.dependency_overrides.clear()

        assert len(body1["data"]) == 2
        assert len(body2["data"]) == 2
        assert body1["total_count"] == 5
        assert body2["total_count"] == 5

        # No overlap between pages
        symbols_p1 = {item["symbol"] for item in body1["data"]}
        symbols_p2 = {item["symbol"] for item in body2["data"]}
        assert symbols_p1.isdisjoint(symbols_p2)

    async def test_last_page_partial_results(self, async_session: AsyncSession) -> None:
        """Last page may have fewer items than page_size."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        for i in range(5):
            await _seed_token(
                async_session,
                symbol=f"T{i}",
                name=f"Token {i}",
                coingecko_id=f"token-{i}",
            )
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?page=3&page_size=2")
        app.dependency_overrides.clear()

        body = response.json()
        assert len(body["data"]) == 1
        assert body["total_count"] == 5

    async def test_page_beyond_data_returns_empty(self, async_session: AsyncSession) -> None:
        """Requesting a page beyond the data must return empty data."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?page=99&page_size=50")
        app.dependency_overrides.clear()

        body = response.json()
        assert body["data"] == []
        assert body["total_count"] == 1

    async def test_rank_numbers_are_page_relative(self, async_session: AsyncSession) -> None:
        """Rank numbers must be absolute (not reset per page)."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        for i in range(4):
            await _seed_token(
                async_session,
                symbol=f"T{i}",
                name=f"Token {i}",
                coingecko_id=f"token-{i}",
                opportunity_score=0.9 - (i * 0.1),
            )
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/opportunities?page=2&page_size=2")
        app.dependency_overrides.clear()

        body = response.json()
        ranks = [item["rank"] for item in body["data"]]
        # Page 2 with size 2: ranks should be 3, 4 (not 1, 2)
        assert ranks == [3, 4]


# ---------------------------------------------------------------------------
# GET /rankings/categories
# ---------------------------------------------------------------------------


class TestGetRankingsCategories:
    """Tests for GET /rankings/categories — distinct categories with counts."""

    async def test_returns_200(self, async_session: AsyncSession) -> None:
        """GET /rankings/categories must return HTTP 200."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/categories")
        app.dependency_overrides.clear()

        assert response.status_code == 200

    async def test_returns_list_of_categories_with_counts(
        self, async_session: AsyncSession
    ) -> None:
        """Response must be a list of {category, count} objects."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="ETH", name="Ethereum", category="l1")
        await _seed_token(async_session, symbol="UNI", name="Uniswap", category="defi")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/categories")
        app.dependency_overrides.clear()

        data = response.json()
        assert isinstance(data, list)

        # Convert to dict for easier assertions
        cat_map = {item["category"]: item["count"] for item in data}
        assert cat_map["l1"] == 2
        assert cat_map["defi"] == 1

    async def test_excludes_null_categories(self, async_session: AsyncSession) -> None:
        """Tokens with null category must not appear in the category list."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        await _seed_token(async_session, symbol="BTC", name="Bitcoin", category="l1")
        await _seed_token(async_session, symbol="NEW", name="NewToken", category=None)
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/categories")
        app.dependency_overrides.clear()

        data = response.json()
        categories = [item["category"] for item in data]
        assert "l1" in categories
        assert None not in categories
        assert len(data) == 1

    async def test_empty_db_returns_empty_list(self, async_session: AsyncSession) -> None:
        """Empty database must return empty list."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/categories")
        app.dependency_overrides.clear()

        assert response.json() == []

    async def test_categories_sorted_by_count_descending(self, async_session: AsyncSession) -> None:
        """Categories must be sorted by token count descending."""
        from app.api.routes.rankings import get_db  # noqa: PLC0415

        # 3 l1 tokens, 2 defi, 1 memecoin
        for i in range(3):
            await _seed_token(
                async_session,
                symbol=f"L{i}",
                name=f"L1 Token {i}",
                coingecko_id=f"l1-{i}",
                category="l1",
            )
        for i in range(2):
            await _seed_token(
                async_session,
                symbol=f"D{i}",
                name=f"DeFi Token {i}",
                coingecko_id=f"defi-{i}",
                category="defi",
            )
        await _seed_token(async_session, symbol="DOGE", name="Dogecoin", category="memecoin")
        await async_session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield async_session

        app.dependency_overrides[get_db] = _override
        client = TestClient(app)
        response = client.get("/rankings/categories")
        app.dependency_overrides.clear()

        data = response.json()
        counts = [item["count"] for item in data]
        assert counts == [3, 2, 1]
