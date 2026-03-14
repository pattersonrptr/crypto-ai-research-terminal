"""Reddit and Twitter/X social metrics collectors."""

from typing import Any

import httpx
import structlog

from app.collectors.base_collector import BaseCollector
from app.exceptions import CollectorError

logger = structlog.get_logger(__name__)


class SocialCollector(BaseCollector):
    """Collector for Reddit social metrics.

    Fetches subreddit subscribers, active users, recent posts count,
    and average post score from the Reddit JSON API.
    """

    def __init__(self, user_agent: str = "CryptoAI/1.0") -> None:
        """Initialize the social collector.

        Args:
            user_agent: User agent string for Reddit API requests.
        """
        super().__init__(base_url="https://www.reddit.com", api_key="")
        self.user_agent = user_agent

    async def __aenter__(self) -> "SocialCollector":
        """Create HTTP client with proper headers for Reddit API."""
        headers: dict[str, str] = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0, headers=headers)
        return self

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Collect metrics for a list of subreddits.

        Args:
            symbols: List of subreddit names (without r/ prefix).

        Returns:
            List of dicts with keys: subreddit, subscribers, active_users,
            posts_24h, avg_score.

        Raises:
            CollectorError: On rate limit (429) or not found (404).
        """
        results: list[dict[str, Any]] = []
        for subreddit in symbols:
            data = await self._fetch_subreddit_data(subreddit)
            results.append(data)
        return results

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Collect metrics for a single subreddit.

        Args:
            symbol: Subreddit name (without r/ prefix).

        Returns:
            Dict with keys: subreddit, subscribers, active_users,
            posts_24h, avg_score.
        """
        result = await self.collect(symbols=[symbol])
        return result[0]

    async def _fetch_subreddit_data(self, subreddit: str) -> dict[str, Any]:
        """Fetch all metrics for a single subreddit.

        Args:
            subreddit: Subreddit name (without r/ prefix).

        Returns:
            Dict with subreddit metrics.

        Raises:
            CollectorError: On HTTP errors.
        """
        log = logger.bind(subreddit=subreddit)
        log.debug("reddit.fetch_subreddit_start")

        try:
            # Fetch subreddit info (subscribers, active users)
            about_data = await self._get(f"/r/{subreddit}/about.json")
            sub_info = about_data.get("data", {})

            # Fetch recent posts
            posts_data = await self._get(f"/r/{subreddit}/new.json")
            posts = posts_data.get("data", {}).get("children", [])

            posts_24h = len(posts)
            total_score = sum(p.get("data", {}).get("score", 0) for p in posts)
            avg_score = total_score / posts_24h if posts_24h > 0 else 0.0

            result = {
                "subreddit": sub_info.get("display_name", subreddit),
                "subscribers": sub_info.get("subscribers", 0),
                "active_users": sub_info.get("active_user_count", 0),
                "posts_24h": posts_24h,
                "avg_score": avg_score,
            }

            log.debug("reddit.fetch_subreddit_complete", **result)
            return result

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429:
                log.warning("reddit.rate_limit", status=status)
                raise CollectorError(f"Reddit rate limit exceeded for r/{subreddit}") from e
            if status == 404:
                log.warning("reddit.not_found", subreddit=subreddit)
                raise CollectorError(f"Subreddit not found: r/{subreddit}") from e
            log.error("reddit.http_error", status=status)
            raise CollectorError(f"Reddit API error {status} for r/{subreddit}") from e


# ---------------------------------------------------------------------------
# TwitterCollector
# ---------------------------------------------------------------------------

_TWITTER_BASE_URL = "https://api.twitter.com/2"


class TwitterCollector(BaseCollector):
    """Collector for Twitter/X mention data.

    Uses the Twitter API v2 ``/tweets/search/recent`` endpoint to count
    recent mentions and compute engagement metrics for a given query.

    Requires a valid ``bearer_token`` from a Twitter Developer App
    (Basic plan or higher).
    """

    def __init__(self, bearer_token: str = "") -> None:
        """Initialise the collector.

        Args:
            bearer_token: Twitter/X API v2 bearer token.
        """
        super().__init__(base_url=_TWITTER_BASE_URL, api_key=bearer_token)

    async def __aenter__(self) -> "TwitterCollector":
        """Create HTTP client with Bearer token auth header."""
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0, headers=headers)
        return self

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Fetch Twitter mention metrics for a list of token symbols.

        Args:
            symbols: List of uppercase token symbols (e.g. ``["SOL", "ETH"]``).

        Returns:
            List of dicts, one per symbol, with keys: ``symbol``,
            ``tweet_count``, ``total_engagement``.
        """
        results: list[dict[str, Any]] = []
        for symbol in symbols:
            query = f"${symbol} OR #{symbol}"
            data = await self.search_mentions(query=query)
            data["symbol"] = symbol
            results.append(data)
        return results

    async def collect_single(self, symbol: str) -> dict[str, Any]:
        """Fetch Twitter mention metrics for a single token symbol.

        Args:
            symbol: Uppercase token symbol (e.g. ``"SOL"``).

        Returns:
            Dict with keys: ``symbol``, ``tweet_count``, ``total_engagement``.
        """
        result = await self.collect(symbols=[symbol])
        return result[0]

    async def search_mentions(
        self,
        query: str,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """Search recent tweets matching *query* and return summary metrics.

        Args:
            query: Twitter search query string.
            max_results: Number of tweets to retrieve (10–100, API limit).

        Returns:
            Dict with keys: ``tweet_count``, ``total_engagement``,
            ``tweets`` (list of raw tweet dicts).

        Raises:
            CollectorError: On 401 Unauthorized, 429 rate limit, or other
                HTTP errors.
        """
        log = logger.bind(query=query)
        log.debug("twitter.search_mentions.start")

        params: dict[str, Any] = {
            "query": query,
            "max_results": max(10, min(max_results, 100)),
            "tweet.fields": "public_metrics,created_at",
        }

        try:
            data: dict[str, Any] = await self._get("/tweets/search/recent", params=params)
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, context=f"search '{query}'")
            raise  # unreachable

        tweets: list[dict[str, Any]] = data.get("data", [])
        tweet_count = len(tweets)
        total_engagement = sum(
            t.get("public_metrics", {}).get("like_count", 0)
            + t.get("public_metrics", {}).get("retweet_count", 0)
            for t in tweets
        )

        result: dict[str, Any] = {
            "tweet_count": tweet_count,
            "total_engagement": total_engagement,
            "tweets": tweets,
        }
        log.debug(
            "twitter.search_mentions.complete",
            tweet_count=tweet_count,
            engagement=total_engagement,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_http_error(exc: httpx.HTTPStatusError, context: str) -> None:
        """Translate HTTPStatusError into CollectorError and raise."""
        status = exc.response.status_code
        if status == 429:
            logger.warning("twitter.rate_limit", context=context)
            raise CollectorError(f"Twitter/X rate limit exceeded ({context})") from exc
        if status == 401:
            logger.warning("twitter.unauthorized", context=context)
            raise CollectorError(
                f"Unauthorized — Invalid Twitter bearer token ({context})"
            ) from exc
        logger.error("twitter.http_error", status=status, context=context)
        raise CollectorError(f"Twitter/X HTTP {status} error ({context})") from exc
