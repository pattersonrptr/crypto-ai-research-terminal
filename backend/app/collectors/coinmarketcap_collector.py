"""CoinMarketCap data collector.

Collects CMC rank, tags, categories, and market data for tokens.
Requires a valid COINMARKETCAP_API_KEY.
"""

from typing import Any

import httpx
import structlog

from app.collectors.base_collector import BaseCollector
from app.exceptions import CollectorError

logger = structlog.get_logger(__name__)

_CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapCollector(BaseCollector):
    """Collector for CoinMarketCap data.

    Fetches CMC rank, tags, categories, and market quote data via the
    CMC Pro API. All requests require a valid ``api_key``.

    Endpoints used:
    - ``/cryptocurrency/listings/latest`` — latest market rankings.
    - ``/cryptocurrency/info`` — metadata (category, tags, description).
    """

    def __init__(self, api_key: str = "") -> None:
        """Initialise the collector.

        Args:
            api_key: CoinMarketCap Pro API key.
        """
        super().__init__(base_url=_CMC_BASE_URL, api_key=api_key)

    async def __aenter__(self) -> "CoinMarketCapCollector":
        """Create HTTP client with CMC auth header."""
        headers: dict[str, str] = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url, timeout=30.0, headers=headers
        )
        return self

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch CMC listings and return normalised token records.

        Args:
            symbols: Optional list of uppercase token symbols to filter
                     (e.g. ``["BTC", "ETH"]``). Pass an empty list to
                     return all tokens from the first page of results.

        Returns:
            List of dicts with keys: ``symbol``, ``name``, ``cmc_rank``,
            ``cmc_id``, ``tags``, ``category``, ``price_usd``,
            ``volume_24h_usd``, ``market_cap_usd``,
            ``percent_change_24h``, ``percent_change_7d``.

        Raises:
            CollectorError: On HTTP errors (429 rate-limit, 401 auth).
        """
        raw = await self._fetch_listings()
        records = [self._normalise(item) for item in raw]
        if symbols:
            upper = {s.upper() for s in symbols}
            records = [r for r in records if r["symbol"] in upper]
        return records

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Fetch CMC data for a single token symbol.

        Args:
            symbol: Uppercase token symbol (e.g. ``"BTC"``).

        Returns:
            Normalised dict for the requested token.

        Raises:
            CollectorError: If the symbol is not found or HTTP error.
        """
        results = await self.collect(symbols=[symbol])
        if not results:
            raise CollectorError(f"Symbol not found in CMC listings: {symbol}")
        return results[0]

    async def fetch_token_info(self, symbol: str) -> dict[str, Any]:
        """Fetch token metadata (category, tags, description, logo).

        Args:
            symbol: Uppercase token symbol (e.g. ``"BTC"``).

        Returns:
            Dict with keys: ``symbol``, ``name``, ``category``,
            ``tags``, ``description``, ``logo``.

        Raises:
            CollectorError: On HTTP errors.
        """
        log = logger.bind(symbol=symbol)
        log.debug("cmc.fetch_info.start")
        try:
            data: dict[str, Any] = await self._get(
                "/cryptocurrency/info", params={"symbol": symbol}
            )
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context=f"info for {symbol}")
            raise  # unreachable — _handle_http_error always raises

        token_data = data.get("data", {}).get(symbol, {})
        result: dict[str, Any] = {
            "symbol": token_data.get("symbol", symbol),
            "name": token_data.get("name", ""),
            "category": token_data.get("category", ""),
            "tags": token_data.get("tags", []),
            "description": token_data.get("description", ""),
            "logo": token_data.get("logo", ""),
        }
        log.debug("cmc.fetch_info.complete", category=result["category"])
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_listings(self) -> list[dict[str, Any]]:
        """Call /cryptocurrency/listings/latest and return raw data list."""
        log = logger.bind(endpoint="listings/latest")
        log.debug("cmc.listings.start")
        try:
            response: dict[str, Any] = await self._get(
                "/cryptocurrency/listings/latest",
                params={"limit": 200, "convert": "USD"},
            )
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context="listings/latest")
            raise  # unreachable — _handle_http_error always raises
        raw: list[dict[str, Any]] = response.get("data", [])
        log.debug("cmc.listings.complete", count=len(raw))
        return raw

    @staticmethod
    def _normalise(item: dict[str, Any]) -> dict[str, Any]:
        """Normalise a single CMC listing entry into a flat dict."""
        quote_usd: dict[str, Any] = item.get("quote", {}).get("USD", {})
        return {
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "cmc_id": item.get("id"),
            "cmc_rank": item.get("cmc_rank"),
            "tags": item.get("tags", []),
            "category": item.get("category", ""),
            "price_usd": quote_usd.get("price"),
            "volume_24h_usd": quote_usd.get("volume_24h"),
            "market_cap_usd": quote_usd.get("market_cap"),
            "percent_change_24h": quote_usd.get("percent_change_24h"),
            "percent_change_7d": quote_usd.get("percent_change_7d"),
        }

    @staticmethod
    def _handle_http_error(exc: httpx.HTTPStatusError, context: str) -> None:
        """Translate HTTPStatusError into CollectorError and raise.

        Args:
            exc: The original HTTP error.
            context: Description string for the log / message.

        Raises:
            CollectorError: Always.
        """
        status = exc.response.status_code
        if status == 429:
            logger.warning("cmc.rate_limit", context=context)
            raise CollectorError(f"CoinMarketCap rate limit exceeded ({context})") from exc
        if status == 401:
            logger.warning("cmc.unauthorized", context=context)
            raise CollectorError(
                f"Unauthorized — Invalid API key for CoinMarketCap ({context})"
            ) from exc
        logger.error("cmc.http_error", status=status, context=context)
        raise CollectorError(
            f"CoinMarketCap HTTP {status} error ({context})"
        ) from exc
