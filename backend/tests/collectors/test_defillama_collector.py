"""Tests for DefiLlamaCollector.

All HTTP calls are mocked with respx — no real network requests are made.
Naming: test_<unit>_<scenario>_<expected_outcome>
"""

import httpx
import pytest
import respx

from app.collectors.defillama_collector import DefiLlamaCollector
from app.exceptions import CollectorError

# ---------------------------------------------------------------------------
# Constants / fixtures
# ---------------------------------------------------------------------------

LLAMA_BASE_URL = "https://api.llama.fi"

# /protocols response (list of all protocols)
LLAMA_PROTOCOLS_RESPONSE: list[dict] = [
    {
        "id": "1",
        "name": "Aave",
        "symbol": "AAVE",
        "slug": "aave",
        "tvl": 12_500_000_000.0,
        "chainTvls": {"Ethereum": 10_000_000_000.0, "Polygon": 2_500_000_000.0},
        "chains": ["Ethereum", "Polygon", "Avalanche"],
        "category": "Lending",
        "change_1d": 1.5,
        "change_7d": 3.2,
        "change_1m": 8.7,
    },
    {
        "id": "2",
        "name": "Uniswap",
        "symbol": "UNI",
        "slug": "uniswap",
        "tvl": 5_800_000_000.0,
        "chainTvls": {"Ethereum": 4_000_000_000.0, "Arbitrum": 1_800_000_000.0},
        "chains": ["Ethereum", "Arbitrum", "Optimism"],
        "category": "Dexes",
        "change_1d": 0.8,
        "change_7d": 2.1,
        "change_1m": 5.4,
    },
]

# /protocol/{slug} detail response
LLAMA_PROTOCOL_DETAIL_RESPONSE: dict = {
    "id": "1",
    "name": "Aave",
    "symbol": "AAVE",
    "slug": "aave",
    "tvl": 12_500_000_000.0,
    "chains": ["Ethereum", "Polygon", "Avalanche"],
    "category": "Lending",
    "currentChainTvls": {"Ethereum": 10_000_000_000.0, "Polygon": 2_500_000_000.0},
    "tvls": [
        {"date": 1_700_000_000, "totalLiquidityUSD": 11_000_000_000.0},
        {"date": 1_702_592_000, "totalLiquidityUSD": 12_500_000_000.0},
    ],
}

# /overview/dexs response (DEX volumes)
LLAMA_DEX_RESPONSE: dict = {
    "protocols": [
        {
            "name": "Uniswap",
            "symbol": "UNI",
            "slug": "uniswap",
            "total24h": 1_200_000_000.0,
            "total7d": 8_400_000_000.0,
            "total30d": 36_000_000_000.0,
        }
    ]
}

# /overview/fees response (revenue)
LLAMA_FEES_RESPONSE: dict = {
    "protocols": [
        {
            "name": "Aave",
            "symbol": "AAVE",
            "slug": "aave",
            "total24h": 500_000.0,
            "total7d": 3_500_000.0,
            "total30d": 15_000_000.0,
        }
    ]
}


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorInit:
    """DefiLlamaCollector initialises with correct base URL."""

    def test_defillama_collector_init_sets_correct_base_url(self) -> None:
        collector = DefiLlamaCollector()
        assert "llama.fi" in collector.base_url

    def test_defillama_collector_init_requires_no_api_key(self) -> None:
        collector = DefiLlamaCollector()
        assert collector.api_key == ""


# ---------------------------------------------------------------------------
# collect() tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorCollect:
    """DefiLlamaCollector.collect() fetches and normalises protocol TVL data."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_returns_list_of_dicts(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=[])
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_returns_tvl(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=[])
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert aave["tvl_usd"] == 12_500_000_000.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_returns_chains(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=[])
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert isinstance(aave["chains"], list)
        assert "Ethereum" in aave["chains"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_returns_category(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=[])
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert aave["category"] == "Lending"

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_returns_tvl_changes(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=[])
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert "tvl_change_1d_pct" in aave
        assert "tvl_change_7d_pct" in aave
        assert "tvl_change_30d_pct" in aave

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_filters_by_symbols_when_provided(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect(symbols=["AAVE"])
        assert len(result) == 1
        assert result[0]["symbol"] == "AAVE"

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_raises_on_server_error(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(CollectorError, match="500|server error"):
            async with DefiLlamaCollector() as collector:
                await collector.collect(symbols=[])


# ---------------------------------------------------------------------------
# collect_single() tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorCollectSingle:
    """DefiLlamaCollector.collect_single() fetches data for one token symbol."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_single_returns_dict(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.collect_single(symbol="AAVE")
        assert isinstance(result, dict)
        assert result["symbol"] == "AAVE"

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_collect_single_raises_when_not_found(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocols").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOLS_RESPONSE)
        )
        with pytest.raises(CollectorError, match="not found"):
            async with DefiLlamaCollector() as collector:
                await collector.collect_single(symbol="UNKNOWN_TOKEN")


# ---------------------------------------------------------------------------
# fetch_protocol_detail() tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorFetchDetail:
    """DefiLlamaCollector.fetch_protocol_detail() fetches historical TVL for a protocol."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_detail_returns_historical_tvl(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocol/aave").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOL_DETAIL_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_protocol_detail(slug="aave")
        assert "historical_tvl" in result
        assert isinstance(result["historical_tvl"], list)

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_detail_returns_chains(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocol/aave").mock(
            return_value=httpx.Response(200, json=LLAMA_PROTOCOL_DETAIL_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_protocol_detail(slug="aave")
        assert "chains" in result
        assert "Ethereum" in result["chains"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_detail_raises_on_not_found(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/protocol/unknown-slug").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(CollectorError, match="not found|404"):
            async with DefiLlamaCollector() as collector:
                await collector.fetch_protocol_detail(slug="unknown-slug")


# ---------------------------------------------------------------------------
# fetch_dex_volumes() tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorFetchDexVolumes:
    """DefiLlamaCollector.fetch_dex_volumes() fetches DEX trading volumes."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_dex_volumes_returns_list(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/dexs").mock(
            return_value=httpx.Response(200, json=LLAMA_DEX_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_dex_volumes()
        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_dex_volumes_returns_24h_volume(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/dexs").mock(
            return_value=httpx.Response(200, json=LLAMA_DEX_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_dex_volumes()
        uni = next(r for r in result if r["symbol"] == "UNI")
        assert uni["volume_24h_usd"] == 1_200_000_000.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_dex_volumes_returns_30d_volume(
        self,
    ) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/dexs").mock(
            return_value=httpx.Response(200, json=LLAMA_DEX_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_dex_volumes()
        uni = next(r for r in result if r["symbol"] == "UNI")
        assert uni["volume_30d_usd"] == 36_000_000_000.0


# ---------------------------------------------------------------------------
# fetch_fees_revenue() tests
# ---------------------------------------------------------------------------


class TestDefiLlamaCollectorFetchFees:
    """DefiLlamaCollector.fetch_fees_revenue() fetches protocol revenue/fees."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_fees_returns_list(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/fees").mock(
            return_value=httpx.Response(200, json=LLAMA_FEES_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_fees_revenue()
        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_fees_returns_24h_revenue(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/fees").mock(
            return_value=httpx.Response(200, json=LLAMA_FEES_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_fees_revenue()
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert aave["revenue_24h_usd"] == 500_000.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_defillama_collector_fetch_fees_returns_30d_revenue(self) -> None:
        respx.get(f"{LLAMA_BASE_URL}/overview/fees").mock(
            return_value=httpx.Response(200, json=LLAMA_FEES_RESPONSE)
        )
        async with DefiLlamaCollector() as collector:
            result = await collector.fetch_fees_revenue()
        aave = next(r for r in result if r["symbol"] == "AAVE")
        assert aave["revenue_30d_usd"] == 15_000_000.0
