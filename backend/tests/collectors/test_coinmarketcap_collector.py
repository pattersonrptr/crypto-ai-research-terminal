"""Tests for CoinMarketCapCollector.

All HTTP calls are mocked with respx — no real network requests are made.
Naming: test_<unit>_<scenario>_<expected_outcome>
"""

import httpx
import pytest
import respx

from app.collectors.coinmarketcap_collector import CoinMarketCapCollector
from app.exceptions import CollectorError

# ---------------------------------------------------------------------------
# Fixtures / constants
# ---------------------------------------------------------------------------

CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

CMC_LISTINGS_RESPONSE: dict = {
    "status": {
        "timestamp": "2025-01-01T00:00:00.000Z",
        "error_code": 0,
        "error_message": None,
        "elapsed": 10,
        "credit_count": 1,
    },
    "data": [
        {
            "id": 1,
            "name": "Bitcoin",
            "symbol": "BTC",
            "slug": "bitcoin",
            "cmc_rank": 1,
            "tags": ["mineable", "pow", "sha-256", "store-of-value"],
            "category": "coin",
            "quote": {
                "USD": {
                    "price": 65000.0,
                    "volume_24h": 35_000_000_000.0,
                    "market_cap": 1_280_000_000_000.0,
                    "percent_change_24h": 1.5,
                    "percent_change_7d": 5.2,
                }
            },
        },
        {
            "id": 1027,
            "name": "Ethereum",
            "symbol": "ETH",
            "slug": "ethereum",
            "cmc_rank": 2,
            "tags": ["mineable", "pow", "smart-contracts", "defi"],
            "category": "coin",
            "quote": {
                "USD": {
                    "price": 3500.0,
                    "volume_24h": 15_000_000_000.0,
                    "market_cap": 420_000_000_000.0,
                    "percent_change_24h": 0.8,
                    "percent_change_7d": 3.1,
                }
            },
        },
    ],
}

CMC_INFO_RESPONSE: dict = {
    "status": {
        "timestamp": "2025-01-01T00:00:00.000Z",
        "error_code": 0,
        "error_message": None,
        "elapsed": 5,
        "credit_count": 1,
    },
    "data": {
        "BTC": {
            "id": 1,
            "name": "Bitcoin",
            "symbol": "BTC",
            "slug": "bitcoin",
            "category": "coin",
            "tags": ["mineable", "pow", "sha-256"],
            "description": "Bitcoin is the first decentralized cryptocurrency.",
            "logo": "https://s2.coinmarketcap.com/static/img/coins/64x64/1.png",
        }
    },
}


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestCoinMarketCapCollectorInit:
    """CoinMarketCapCollector initialises with correct base URL and API key."""

    def test_coinmarketcap_collector_init_sets_correct_base_url(self) -> None:
        collector = CoinMarketCapCollector(api_key="test-key")
        assert "coinmarketcap.com" in collector.base_url

    def test_coinmarketcap_collector_init_stores_api_key(self) -> None:
        collector = CoinMarketCapCollector(api_key="my-secret-key")
        assert collector.api_key == "my-secret-key"

    def test_coinmarketcap_collector_init_empty_api_key_by_default(self) -> None:
        collector = CoinMarketCapCollector()
        assert collector.api_key == ""


# ---------------------------------------------------------------------------
# collect() tests
# ---------------------------------------------------------------------------


class TestCoinMarketCapCollectorCollect:
    """CoinMarketCapCollector.collect() fetches and normalises CMC listings data."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_list_of_dicts(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_cmc_rank(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        btc = next(r for r in result if r["symbol"] == "BTC")
        assert btc["cmc_rank"] == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_tags(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        btc = next(r for r in result if r["symbol"] == "BTC")
        assert isinstance(btc["tags"], list)
        assert "mineable" in btc["tags"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_category(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        btc = next(r for r in result if r["symbol"] == "BTC")
        assert btc["category"] == "coin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_usd_price(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        eth = next(r for r in result if r["symbol"] == "ETH")
        assert eth["price_usd"] == 3500.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_returns_market_cap(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=[])
        btc = next(r for r in result if r["symbol"] == "BTC")
        assert btc["market_cap_usd"] == 1_280_000_000_000.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_filters_by_symbols_when_provided(
        self,
    ) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect(symbols=["BTC"])
        assert len(result) == 1
        assert result[0]["symbol"] == "BTC"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_raises_on_rate_limit(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(429)
        )
        with pytest.raises(CollectorError, match="rate limit"):
            async with CoinMarketCapCollector(api_key="test-key") as collector:
                await collector.collect(symbols=[])

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_raises_on_unauthorized(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(401)
        )
        with pytest.raises(CollectorError, match="[Uu]nauthorized|[Ii]nvalid API key|401"):
            async with CoinMarketCapCollector(api_key="bad-key") as collector:
                await collector.collect(symbols=[])


# ---------------------------------------------------------------------------
# collect_single() tests
# ---------------------------------------------------------------------------


class TestCoinMarketCapCollectorCollectSingle:
    """CoinMarketCapCollector.collect_single() fetches info for one token symbol."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_single_returns_dict(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect_single(symbol="BTC")
        assert isinstance(result, dict)
        assert result["symbol"] == "BTC"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_single_returns_cmc_rank(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.collect_single(symbol="BTC")
        assert result["cmc_rank"] == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_collect_single_raises_when_symbol_not_found(
        self,
    ) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/listings/latest").mock(
            return_value=httpx.Response(200, json=CMC_LISTINGS_RESPONSE)
        )
        with pytest.raises(CollectorError, match="not found"):
            async with CoinMarketCapCollector(api_key="test-key") as collector:
                await collector.collect_single(symbol="UNKNOWN_XYZ")


# ---------------------------------------------------------------------------
# fetch_token_info() tests (metadata endpoint)
# ---------------------------------------------------------------------------


class TestCoinMarketCapCollectorFetchInfo:
    """CoinMarketCapCollector.fetch_token_info() fetches metadata from /info endpoint."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_fetch_info_returns_category(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/info").mock(
            return_value=httpx.Response(200, json=CMC_INFO_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.fetch_token_info(symbol="BTC")
        assert result["category"] == "coin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_fetch_info_returns_tags_list(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/info").mock(
            return_value=httpx.Response(200, json=CMC_INFO_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.fetch_token_info(symbol="BTC")
        assert "tags" in result
        assert isinstance(result["tags"], list)

    @pytest.mark.asyncio
    @respx.mock
    async def test_coinmarketcap_collector_fetch_info_returns_description(self) -> None:
        respx.get(f"{CMC_BASE_URL}/cryptocurrency/info").mock(
            return_value=httpx.Response(200, json=CMC_INFO_RESPONSE)
        )
        async with CoinMarketCapCollector(api_key="test-key") as collector:
            result = await collector.fetch_token_info(symbol="BTC")
        assert "description" in result
        assert len(result["description"]) > 0
