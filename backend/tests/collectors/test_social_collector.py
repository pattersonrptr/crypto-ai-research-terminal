"""TDD tests for SocialCollector — Reddit social metrics."""

import httpx
import pytest
import respx

from app.collectors.social_collector import SocialCollector
from app.exceptions import CollectorError


class TestSocialCollectorInit:
    """Tests for SocialCollector initialization."""

    def test_init_sets_reddit_base_url(self) -> None:
        """SocialCollector must set Reddit API base URL."""
        collector = SocialCollector()
        assert collector.base_url == "https://www.reddit.com"

    def test_init_accepts_user_agent(self) -> None:
        """SocialCollector must accept a custom user agent."""
        collector = SocialCollector(user_agent="TestApp/1.0")
        assert collector.user_agent == "TestApp/1.0"


class TestSocialCollectorCollect:
    """Tests for SocialCollector.collect() method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_returns_list(self) -> None:
        """collect() must return a list of subreddit data dicts."""
        respx.get("https://www.reddit.com/r/solana/about.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "display_name": "solana",
                        "subscribers": 250000,
                        "active_user_count": 1500,
                    }
                },
            )
        )
        respx.get("https://www.reddit.com/r/solana/new.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            {"data": {"score": 100, "num_comments": 20}},
                            {"data": {"score": 50, "num_comments": 10}},
                        ]
                    }
                },
            )
        )

        collector = SocialCollector()
        async with collector:
            result = await collector.collect(symbols=["solana"])

        assert isinstance(result, list)
        assert len(result) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_returns_required_fields(self) -> None:
        """collect() must return dicts with subreddit, subscribers, posts_24h, avg_score."""
        respx.get("https://www.reddit.com/r/ethereum/about.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "display_name": "ethereum",
                        "subscribers": 2000000,
                        "active_user_count": 5000,
                    }
                },
            )
        )
        respx.get("https://www.reddit.com/r/ethereum/new.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            {"data": {"score": 200, "num_comments": 50}},
                            {"data": {"score": 100, "num_comments": 30}},
                            {"data": {"score": 50, "num_comments": 10}},
                        ]
                    }
                },
            )
        )

        collector = SocialCollector()
        async with collector:
            result = await collector.collect(symbols=["ethereum"])

        item = result[0]
        assert item["subreddit"] == "ethereum"
        assert item["subscribers"] == 2000000
        assert item["active_users"] == 5000
        assert item["posts_24h"] == 3
        assert item["avg_score"] == 350 / 3  # Average of 200+100+50

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_handles_empty_posts(self) -> None:
        """collect() must handle subreddits with no recent posts."""
        respx.get("https://www.reddit.com/r/newcoin/about.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "display_name": "newcoin",
                        "subscribers": 100,
                        "active_user_count": 5,
                    }
                },
            )
        )
        respx.get("https://www.reddit.com/r/newcoin/new.json").mock(
            return_value=httpx.Response(200, json={"data": {"children": []}})
        )

        collector = SocialCollector()
        async with collector:
            result = await collector.collect(symbols=["newcoin"])

        assert result[0]["posts_24h"] == 0
        assert result[0]["avg_score"] == 0.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_handles_rate_limit_error(self) -> None:
        """collect() must raise CollectorError on 429 rate limit."""
        respx.get("https://www.reddit.com/r/test/about.json").mock(
            return_value=httpx.Response(429, json={"message": "Too Many Requests"})
        )

        collector = SocialCollector()
        async with collector:
            with pytest.raises(CollectorError):
                await collector.collect(symbols=["test"])

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_handles_not_found(self) -> None:
        """collect() must raise CollectorError on 404 for non-existent subreddit."""
        respx.get("https://www.reddit.com/r/nonexistent123/about.json").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        collector = SocialCollector()
        async with collector:
            with pytest.raises(CollectorError):
                await collector.collect(symbols=["nonexistent123"])


class TestSocialCollectorCollectSingle:
    """Tests for SocialCollector.collect_single() method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_single_returns_dict(self) -> None:
        """collect_single() must return a single subreddit data dict."""
        respx.get("https://www.reddit.com/r/bitcoin/about.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "display_name": "bitcoin",
                        "subscribers": 5000000,
                        "active_user_count": 10000,
                    }
                },
            )
        )
        respx.get("https://www.reddit.com/r/bitcoin/new.json").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"children": [{"data": {"score": 500, "num_comments": 100}}]}},
            )
        )

        collector = SocialCollector()
        async with collector:
            result = await collector.collect_single(symbol="bitcoin")

        assert isinstance(result, dict)
        assert result["subreddit"] == "bitcoin"
        assert result["subscribers"] == 5000000
