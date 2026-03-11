"""CoinGecko collector — fetches market data from the CoinGecko public API."""

from typing import Any

import structlog

from app.collectors.base_collector import BaseCollector
from app.exceptions import CollectorError

logger = structlog.get_logger(__name__)

_COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
_MARKETS_ENDPOINT = "/coins/markets"
_DEFAULT_PAGE_SIZE = 250


class CoinGeckoCollector(BaseCollector):
    """Collects price, market cap, volume, rank, ATH and supply data from CoinGecko."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__(base_url=_COINGECKO_BASE_URL, api_key=api_key)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch market data for the given list of CoinGecko IDs.

        Args:
            symbols: CoinGecko coin IDs (e.g. ``["bitcoin", "ethereum"]``).

        Returns:
            List of normalised market-data dicts.

        Raises:
            CollectorError: If the HTTP request fails or the response is invalid.
        """
        params: dict[str, Any] = {
            "vs_currency": "usd",
            "ids": ",".join(symbols),
            "order": "market_cap_desc",
            "per_page": _DEFAULT_PAGE_SIZE,
            "page": 1,
            "sparkline": False,
        }
        if self.api_key:
            params["x_cg_pro_api_key"] = self.api_key

        try:
            raw: list[dict[str, Any]] = await self._get(_MARKETS_ENDPOINT, params=params)
        except Exception as exc:
            logger.error("coingecko.collect.failed", error=str(exc))
            raise CollectorError(f"CoinGecko collect failed: {exc}") from exc

        return [self._normalise(record) for record in raw]

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Fetch market data for a single CoinGecko coin ID.

        Args:
            symbol: CoinGecko coin ID (e.g. ``"bitcoin"``).

        Returns:
            Normalised market-data dict.

        Raises:
            CollectorError: If the token is not found or the request fails.
        """
        results = await self.collect([symbol])
        if not results:
            raise CollectorError(f"CoinGecko returned no data for '{symbol}'")
        return results[0]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(raw: dict[str, Any]) -> dict[str, Any]:
        """Map a raw CoinGecko markets record to the platform's internal schema."""
        return {
            "coingecko_id": raw["id"],
            "symbol": raw["symbol"],
            "name": raw["name"],
            "price_usd": raw.get("current_price") or 0.0,
            "market_cap_usd": raw.get("market_cap") or 0.0,
            "volume_24h_usd": raw.get("total_volume") or 0.0,
            "rank": raw.get("market_cap_rank"),
            "ath_usd": raw.get("ath"),
            "circulating_supply": raw.get("circulating_supply"),
        }
