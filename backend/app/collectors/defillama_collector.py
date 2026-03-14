"""DefiLlama data collector.

Collects TVL, TVL evolution, chains, DEX volume, and protocol revenue.
DefiLlama is a free API — no API key required.
"""

from typing import Any

import httpx
import structlog

from app.collectors.base_collector import BaseCollector
from app.exceptions import CollectorError

logger = structlog.get_logger(__name__)

_LLAMA_BASE_URL = "https://api.llama.fi"


class DefiLlamaCollector(BaseCollector):
    """Collector for DefiLlama DeFi data.

    Fetches TVL, TVL evolution (1d/7d/30d change), chains, DEX volume,
    and protocol revenue from the public DefiLlama API.

    Endpoints used:
    - ``/protocols`` — all protocols with TVL summary.
    - ``/protocol/{slug}`` — detailed historical TVL for one protocol.
    - ``/overview/dexs`` — DEX trading volumes.
    - ``/overview/fees`` — protocol fees/revenue.
    """

    def __init__(self) -> None:
        """Initialise the collector (no API key needed)."""
        super().__init__(base_url=_LLAMA_BASE_URL, api_key="")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch TVL data for all known DeFi protocols.

        Args:
            symbols: Optional list of uppercase token symbols to filter
                     (e.g. ``["AAVE", "UNI"]``). Pass an empty list to
                     return all protocols.

        Returns:
            List of dicts with keys: ``symbol``, ``name``, ``slug``,
            ``tvl_usd``, ``chains``, ``category``, ``tvl_change_1d_pct``,
            ``tvl_change_7d_pct``, ``tvl_change_30d_pct``.

        Raises:
            CollectorError: On HTTP errors.
        """
        raw = await self._fetch_protocols()
        records = [self._normalise_protocol(p) for p in raw]
        if symbols:
            upper = {s.upper() for s in symbols}
            records = [r for r in records if r["symbol"].upper() in upper]
        return records

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Fetch TVL data for a single token symbol.

        Args:
            symbol: Uppercase token symbol (e.g. ``"AAVE"``).

        Returns:
            Normalised dict for the requested token.

        Raises:
            CollectorError: If the symbol is not found or HTTP error.
        """
        results = await self.collect(symbols=[symbol])
        if not results:
            raise CollectorError(f"Symbol not found in DefiLlama protocols: {symbol}")
        return results[0]

    async def fetch_protocol_detail(self, slug: str) -> dict[str, Any]:
        """Fetch detailed historical TVL for a protocol slug.

        Args:
            slug: DefiLlama protocol slug (e.g. ``"aave"``).

        Returns:
            Dict with keys: ``slug``, ``chains``, ``tvl_usd``,
            ``historical_tvl`` (list of ``{date, tvl_usd}``).

        Raises:
            CollectorError: On HTTP errors including 404.
        """
        log = logger.bind(slug=slug)
        log.debug("defillama.fetch_detail.start")
        try:
            data: dict[str, Any] = await self._get(f"/protocol/{slug}")
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context=f"protocol/{slug}")
            raise  # unreachable

        historical_tvl = [
            {"date": entry.get("date"), "tvl_usd": entry.get("totalLiquidityUSD")}
            for entry in data.get("tvls", [])
        ]
        result: dict[str, Any] = {
            "slug": slug,
            "tvl_usd": data.get("tvl"),
            "chains": data.get("chains", []),
            "historical_tvl": historical_tvl,
        }
        log.debug("defillama.fetch_detail.complete", tvl=result["tvl_usd"])
        return result

    async def fetch_dex_volumes(self) -> list[dict[str, Any]]:
        """Fetch DEX trading volume summary for all protocols.

        Returns:
            List of dicts with keys: ``symbol``, ``name``, ``slug``,
            ``volume_24h_usd``, ``volume_7d_usd``, ``volume_30d_usd``.

        Raises:
            CollectorError: On HTTP errors.
        """
        log = logger.bind(endpoint="overview/dexs")
        log.debug("defillama.dex_volumes.start")
        try:
            data: dict[str, Any] = await self._get("/overview/dexs")
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context="overview/dexs")
            raise  # unreachable

        protocols: list[dict[str, Any]] = data.get("protocols", [])
        result = [self._normalise_dex(p) for p in protocols]
        log.debug("defillama.dex_volumes.complete", count=len(result))
        return result

    async def fetch_fees_revenue(self) -> list[dict[str, Any]]:
        """Fetch protocol fees/revenue summary for all protocols.

        Returns:
            List of dicts with keys: ``symbol``, ``name``, ``slug``,
            ``revenue_24h_usd``, ``revenue_7d_usd``, ``revenue_30d_usd``.

        Raises:
            CollectorError: On HTTP errors.
        """
        log = logger.bind(endpoint="overview/fees")
        log.debug("defillama.fees.start")
        try:
            data: dict[str, Any] = await self._get("/overview/fees")
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context="overview/fees")
            raise  # unreachable

        protocols: list[dict[str, Any]] = data.get("protocols", [])
        result = [self._normalise_fees(p) for p in protocols]
        log.debug("defillama.fees.complete", count=len(result))
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_protocols(self) -> list[dict[str, Any]]:
        """Call /protocols and return raw list."""
        log = logger.bind(endpoint="protocols")
        log.debug("defillama.protocols.start")
        try:
            data: list[dict[str, Any]] = await self._get("/protocols")
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context="protocols")
            raise  # unreachable
        log.debug("defillama.protocols.complete", count=len(data))
        return data

    @staticmethod
    def _normalise_protocol(item: dict[str, Any]) -> dict[str, Any]:
        """Normalise a /protocols list entry into a flat dict."""
        return {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "slug": item.get("slug", ""),
            "tvl_usd": item.get("tvl"),
            "chains": item.get("chains", []),
            "category": item.get("category", ""),
            "tvl_change_1d_pct": item.get("change_1d"),
            "tvl_change_7d_pct": item.get("change_7d"),
            "tvl_change_30d_pct": item.get("change_1m"),
        }

    @staticmethod
    def _normalise_dex(item: dict[str, Any]) -> dict[str, Any]:
        """Normalise a /overview/dexs protocol entry."""
        return {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "slug": item.get("slug", ""),
            "volume_24h_usd": item.get("total24h"),
            "volume_7d_usd": item.get("total7d"),
            "volume_30d_usd": item.get("total30d"),
        }

    @staticmethod
    def _normalise_fees(item: dict[str, Any]) -> dict[str, Any]:
        """Normalise a /overview/fees protocol entry."""
        return {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "slug": item.get("slug", ""),
            "revenue_24h_usd": item.get("total24h"),
            "revenue_7d_usd": item.get("total7d"),
            "revenue_30d_usd": item.get("total30d"),
        }

    @staticmethod
    def _handle_http_error(exc: httpx.HTTPStatusError, context: str) -> None:
        """Translate HTTPStatusError into CollectorError and raise.

        Args:
            exc: The original HTTP error.
            context: Description string for logging.

        Raises:
            CollectorError: Always.
        """
        status = exc.response.status_code
        if status == 404:
            logger.warning("defillama.not_found", context=context)
            raise CollectorError(
                f"DefiLlama resource not found ({context})"
            ) from exc
        logger.error("defillama.http_error", status=status, context=context)
        raise CollectorError(
            f"DefiLlama HTTP {status} server error ({context})"
        ) from exc
