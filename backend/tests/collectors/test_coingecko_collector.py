"""Tests for CoinGeckoCollector.

All HTTP calls are mocked with respx — no real network requests are made.
"""

import httpx
import pytest
import respx

from app.collectors.coingecko_collector import CoinGeckoCollector
from app.exceptions import CollectorError

COINGECKO_MARKETS_RESPONSE = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 65000.0,
        "market_cap": 1_280_000_000_000,
        "total_volume": 35_000_000_000,
        "market_cap_rank": 1,
        "ath": 73_750.0,
        "circulating_supply": 19_700_000.0,
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "current_price": 3500.0,
        "market_cap": 420_000_000_000,
        "total_volume": 15_000_000_000,
        "market_cap_rank": 2,
        "ath": 4_878.0,
        "circulating_supply": 120_000_000.0,
    },
]


class TestCoinGeckoCollectorInit:
    """CoinGeckoCollector initialises with correct base URL and optional API key."""

    def test_coingecko_collector_init_sets_base_url(self) -> None:
        collector = CoinGeckoCollector()
        assert "coingecko.com" in collector.base_url

    def test_coingecko_collector_init_accepts_api_key(self) -> None:
        collector = CoinGeckoCollector(api_key="test-key")
        assert collector.api_key == "test-key"

    def test_coingecko_collector_init_empty_api_key_by_default(self) -> None:
        collector = CoinGeckoCollector()
        assert collector.api_key == ""


class TestCoinGeckoCollectorCollect:
    """CoinGeckoCollector.collect() fetches and normalises market data."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_returns_list_of_market_data(self) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(200, json=COINGECKO_MARKETS_RESPONSE))

        async with CoinGeckoCollector() as collector:
            results = await collector.collect(["bitcoin", "ethereum"])

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_result_has_required_fields(self) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(200, json=COINGECKO_MARKETS_RESPONSE))

        async with CoinGeckoCollector() as collector:
            results = await collector.collect(["bitcoin"])

        record = results[0]
        assert {
            "coingecko_id",
            "symbol",
            "name",
            "price_usd",
            "market_cap_usd",
            "volume_24h_usd",
            "rank",
            "ath_usd",
            "circulating_supply",
        }.issubset(record.keys())

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_maps_price_correctly(self) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(200, json=COINGECKO_MARKETS_RESPONSE))

        async with CoinGeckoCollector() as collector:
            results = await collector.collect(["bitcoin"])

        assert results[0]["price_usd"] == 65000.0
        assert results[0]["symbol"] == "btc"
        assert results[0]["coingecko_id"] == "bitcoin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_raises_collector_error_on_http_error(
        self,
    ) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(429))

        with pytest.raises(CollectorError):
            async with CoinGeckoCollector() as collector:
                await collector.collect(["bitcoin"])


class TestCoinGeckoCollectorCollectSingle:
    """CoinGeckoCollector.collect_single() fetches data for one token."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_single_returns_dict(self) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(200, json=[COINGECKO_MARKETS_RESPONSE[0]]))

        async with CoinGeckoCollector() as collector:
            result = await collector.collect_single("bitcoin")

        assert isinstance(result, dict)
        assert result["coingecko_id"] == "bitcoin"

    @pytest.mark.asyncio
    @respx.mock
    async def test_coingecko_collector_collect_single_raises_collector_error_when_not_found(
        self,
    ) -> None:
        respx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
        ).mock(return_value=httpx.Response(200, json=[]))

        with pytest.raises(CollectorError):
            async with CoinGeckoCollector() as collector:
                await collector.collect_single("nonexistent-token")


# ── Detail-based data (coin detail pages with categories) ──────────────────

COINGECKO_DETAIL_BITCOIN = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "categories": ["Cryptocurrency", "Layer 1 (L1)", "Proof of Work (PoW)"],
}

COINGECKO_DETAIL_ETHEREUM = {
    "id": "ethereum",
    "symbol": "eth",
    "name": "Ethereum",
    "categories": ["Smart Contract Platform", "Layer 1 (L1)"],
}

COINGECKO_DETAIL_AAVE = {
    "id": "aave",
    "symbol": "aave",
    "name": "Aave",
    "categories": ["DeFi", "Lending/Borrowing"],
}


class TestCoinGeckoCollectorCollectCategories:
    """CoinGeckoCollector.collect_categories() fetches categories via /coins/{id}."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_collect_categories_returns_dict_mapping_id_to_categories(
        self,
    ) -> None:
        respx.get("https://api.coingecko.com/api/v3/coins/bitcoin").mock(
            return_value=httpx.Response(200, json=COINGECKO_DETAIL_BITCOIN)
        )
        respx.get("https://api.coingecko.com/api/v3/coins/ethereum").mock(
            return_value=httpx.Response(200, json=COINGECKO_DETAIL_ETHEREUM)
        )

        async with CoinGeckoCollector() as collector:
            result = await collector.collect_categories(["bitcoin", "ethereum"])

        assert isinstance(result, dict)
        assert "bitcoin" in result
        assert "ethereum" in result
        assert "Layer 1 (L1)" in result["bitcoin"]
        assert "Smart Contract Platform" in result["ethereum"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_collect_categories_skips_failed_tokens(self) -> None:
        respx.get("https://api.coingecko.com/api/v3/coins/bitcoin").mock(
            return_value=httpx.Response(200, json=COINGECKO_DETAIL_BITCOIN)
        )
        respx.get("https://api.coingecko.com/api/v3/coins/nonexistent").mock(
            return_value=httpx.Response(404)
        )

        async with CoinGeckoCollector() as collector:
            result = await collector.collect_categories(["bitcoin", "nonexistent"], delay=0.0)

        assert "bitcoin" in result
        assert "nonexistent" not in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_collect_categories_empty_input_returns_empty_dict(self) -> None:
        async with CoinGeckoCollector() as collector:
            result = await collector.collect_categories([])

        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_collect_categories_handles_missing_categories_field(self) -> None:
        respx.get("https://api.coingecko.com/api/v3/coins/bitcoin").mock(
            return_value=httpx.Response(200, json={"id": "bitcoin", "symbol": "btc"})
        )

        async with CoinGeckoCollector() as collector:
            result = await collector.collect_categories(["bitcoin"], delay=0.0)

        assert result["bitcoin"] == []
