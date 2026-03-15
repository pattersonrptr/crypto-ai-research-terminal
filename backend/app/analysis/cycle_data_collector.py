"""CycleDataCollector — fetches market cycle indicator data from external APIs.

Sources:
- Fear & Greed Index: Alternative.me API (free, no key required)
- BTC Dominance + Total Market Cap: CoinGecko ``/global`` endpoint
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.analysis.cycle_detector import CycleIndicators

logger = structlog.get_logger(__name__)

_FEAR_GREED_URL = "https://api.alternative.me/fng/"
_COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"

# Defaults when APIs are unavailable
_DEFAULT_FG_INDEX = 50
_DEFAULT_FG_LABEL = "unavailable"
_DEFAULT_BTC_DOMINANCE = 50.0
_DEFAULT_TOTAL_MCAP = 0.0


class CycleDataCollector:
    """Collects market cycle indicator data from public APIs.

    All methods are resilient: on failure they return safe defaults
    and log a warning rather than raising exceptions.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def _http_get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an HTTP GET and return parsed JSON.

        Args:
            url: Full URL to request.
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            Exception: On any HTTP or parsing error.
        """
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Fear & Greed Index (Alternative.me)
    # ------------------------------------------------------------------

    async def fetch_fear_greed(self) -> tuple[int, str]:
        """Fetch the current Fear & Greed index value.

        Returns:
            Tuple of (index: int, label: str). On failure returns
            (50, 'unavailable').
        """
        try:
            data = await self._http_get(_FEAR_GREED_URL, params={"limit": 1})
            entry = data["data"][0]
            index = int(entry["value"])
            label = str(entry["value_classification"])
            logger.info("cycle.fear_greed.fetched", index=index, label=label)
            return index, label
        except Exception:
            logger.warning("cycle.fear_greed.failed")
            return _DEFAULT_FG_INDEX, _DEFAULT_FG_LABEL

    # ------------------------------------------------------------------
    # BTC Dominance + Total Market Cap (CoinGecko /global)
    # ------------------------------------------------------------------

    async def fetch_btc_dominance(self) -> tuple[float, float]:
        """Fetch current BTC dominance percentage and total crypto market cap.

        Returns:
            Tuple of (btc_dominance: float, total_market_cap_usd: float).
            On failure returns (50.0, 0.0).
        """
        try:
            data = await self._http_get(_COINGECKO_GLOBAL_URL)
            btc_dom = float(data["data"]["market_cap_percentage"]["btc"])
            total_mcap = float(data["data"]["total_market_cap"]["usd"])
            logger.info(
                "cycle.btc_dominance.fetched",
                btc_dominance=round(btc_dom, 2),
                total_mcap=total_mcap,
            )
            return btc_dom, total_mcap
        except Exception:
            logger.warning("cycle.btc_dominance.failed")
            return _DEFAULT_BTC_DOMINANCE, _DEFAULT_TOTAL_MCAP

    # ------------------------------------------------------------------
    # Full indicator assembly
    # ------------------------------------------------------------------

    async def collect_indicators(
        self,
        btc_dominance_30d_ago: float,
        total_market_cap_200d_ma: float | None = None,
    ) -> CycleIndicators:
        """Collect all indicators and assemble a :class:`CycleIndicators`.

        Args:
            btc_dominance_30d_ago: BTC dominance 30 days ago (stored in DB).
            total_market_cap_200d_ma: 200-day MA of total market cap.
                ``None`` when historical data is unavailable.

        Returns:
            Populated :class:`CycleIndicators` instance.
        """
        fg_index, fg_label = await self.fetch_fear_greed()
        btc_dom, total_mcap = await self.fetch_btc_dominance()

        return CycleIndicators(
            btc_dominance=btc_dom,
            btc_dominance_30d_ago=btc_dominance_30d_ago,
            total_market_cap_usd=total_mcap,
            total_market_cap_200d_ma=total_market_cap_200d_ma,
            fear_greed_index=fg_index,
            fear_greed_label=fg_label,
        )
