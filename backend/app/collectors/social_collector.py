"""Reddit social metrics collector."""

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
