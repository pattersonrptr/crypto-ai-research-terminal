"""Base collector class — all collectors inherit from this."""

import abc
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class BaseCollector(abc.ABC):
    """Abstract base for all external data collectors.

    Provides automatic retry with exponential backoff, rate limiting
    awareness, and structured logging.
    """

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseCollector":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request with automatic retry."""
        assert self._client is not None, "Use collector as an async context manager"
        log = logger.bind(path=path, params=params)
        log.debug("collector.request")
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        log.debug("collector.response", status=response.status_code)
        return response.json()

    @abc.abstractmethod
    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Collect data for a list of token symbols."""

    @abc.abstractmethod
    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Collect data for a single token symbol."""
