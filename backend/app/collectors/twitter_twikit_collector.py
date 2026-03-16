"""Twitter/X data collector using twikit (free, no API key required).

Uses the twikit library to scrape Twitter/X data with a regular account.
Requires TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD in .env.
Persists cookies to avoid repeated logins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TwitterTwikitCollector:
    """Collector for Twitter/X mention data using twikit (free scraping).

    Unlike the TwitterCollector (which requires a paid API bearer token),
    this collector uses twikit to scrape Twitter with a regular X account.

    Features:
    - Login with email/password (no API key needed).
    - Cookie persistence to avoid repeated logins.
    - Search for $SYMBOL mentions in recent tweets.
    - Rate-limit aware via configurable delay.
    """

    def __init__(
        self,
        username: str = "",
        email: str = "",
        password: str = "",
        cookies_path: str = "twitter_cookies.json",
    ) -> None:
        """Initialise the collector.

        Args:
            username: Twitter/X username (without @).
            email: Twitter/X account email address.
            password: Twitter/X account password.
            cookies_path: File path to persist login cookies.
        """
        self.username = username
        self.email = email
        self.password = password
        self.cookies_path = cookies_path
        self._client: Any = None

    async def _ensure_client(self) -> Any:
        """Lazily create the twikit Client if not yet initialised."""
        if self._client is None:
            from twikit import Client  # noqa: PLC0415

            self._client = Client("en-US")
        return self._client

    async def login(self) -> None:
        """Login to Twitter/X — load cookies if available, else fresh login.

        After a fresh login the cookies are saved to ``cookies_path``
        so subsequent runs skip the login step.
        """
        client = await self._ensure_client()
        log = logger.bind(username=self.username)

        cookies_file = Path(self.cookies_path)
        if cookies_file.exists():
            log.debug("twitter_twikit.login.loading_cookies", path=self.cookies_path)
            client.load_cookies(self.cookies_path)
            return

        log.info("twitter_twikit.login.fresh_login")
        await client.login(
            auth_info_1=self.username,
            auth_info_2=self.email,
            password=self.password,
        )
        client.save_cookies(self.cookies_path)
        log.info("twitter_twikit.login.cookies_saved", path=self.cookies_path)

    async def collect_mentions(self, symbol: str) -> dict[str, Any]:
        """Search for recent mentions of a token symbol.

        Args:
            symbol: Uppercase token symbol (e.g. ``"BTC"``).

        Returns:
            Dict with keys: ``symbol``, ``mention_count``,
            ``total_engagement``, ``texts`` (list of raw tweet texts).
        """
        client = await self._ensure_client()
        log = logger.bind(symbol=symbol)
        log.debug("twitter_twikit.collect_mentions.start")

        query = f"${symbol} OR #{symbol}"
        search_result = await client.search_tweet(query, "Latest")

        tweets_list: list[Any] = list(search_result)
        mention_count = len(tweets_list)

        total_engagement = sum(
            getattr(t, "favorite_count", 0) + getattr(t, "retweet_count", 0)
            for t in tweets_list
        )

        texts = [getattr(t, "text", "") for t in tweets_list]

        result: dict[str, Any] = {
            "symbol": symbol,
            "mention_count": mention_count,
            "total_engagement": total_engagement,
            "texts": texts,
        }

        log.debug(
            "twitter_twikit.collect_mentions.complete",
            mention_count=mention_count,
            engagement=total_engagement,
        )
        return result

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Collect mention metrics for a list of token symbols.

        Args:
            symbols: List of uppercase token symbols.

        Returns:
            List of mention dicts, one per symbol.
        """
        results: list[dict[str, Any]] = []
        for symbol in symbols:
            data = await self.collect_mentions(symbol)
            results.append(data)
        return results

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Collect mention metrics for a single token symbol.

        Args:
            symbol: Uppercase token symbol.

        Returns:
            Dict with mention metrics.
        """
        return await self.collect_mentions(symbol)
