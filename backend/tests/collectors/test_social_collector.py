"""TDD tests for SocialCollector — Reddit + Twitter/X social metrics."""

import httpx
import pytest
import respx

from app.collectors.social_collector import SocialCollector, TwitterCollector
from app.exceptions import CollectorError

# ---------------------------------------------------------------------------
# Twitter/X mock data
# ---------------------------------------------------------------------------

TWITTER_BASE_URL = "https://api.twitter.com/2"

TWITTER_SEARCH_RESPONSE: dict = {
    "data": [
        {
            "id": "1001",
            "text": "Solana is amazing! $SOL is going to the moon 🚀",
            "public_metrics": {
                "like_count": 150,
                "retweet_count": 45,
                "reply_count": 20,
                "impression_count": 5000,
            },
            "created_at": "2025-01-01T12:00:00.000Z",
        },
        {
            "id": "1002",
            "text": "Just bought more $SOL, bullish on Solana",
            "public_metrics": {
                "like_count": 80,
                "retweet_count": 22,
                "reply_count": 10,
                "impression_count": 2000,
            },
            "created_at": "2025-01-01T11:00:00.000Z",
        },
    ],
    "meta": {
        "newest_id": "1002",
        "oldest_id": "1001",
        "result_count": 2,
        "next_token": None,
    },
}

TWITTER_SEARCH_EMPTY_RESPONSE: dict = {
    "meta": {
        "result_count": 0,
    }
}


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


# ---------------------------------------------------------------------------
# TwitterCollector tests
# ---------------------------------------------------------------------------


class TestTwitterCollectorInit:
    """TwitterCollector initialises with correct base URL and bearer token."""

    def test_twitter_collector_init_sets_correct_base_url(self) -> None:
        collector = TwitterCollector(bearer_token="test-token")
        assert "api.twitter.com" in collector.base_url

    def test_twitter_collector_init_stores_bearer_token(self) -> None:
        collector = TwitterCollector(bearer_token="my-bearer-token")
        assert collector.api_key == "my-bearer-token"

    def test_twitter_collector_init_empty_token_by_default(self) -> None:
        collector = TwitterCollector()
        assert collector.api_key == ""


class TestTwitterCollectorSearchMentions:
    """TwitterCollector.search_mentions() fetches recent tweet mentions for a query."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_returns_dict(self) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.search_mentions(query="$SOL Solana")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_returns_tweet_count(self) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.search_mentions(query="$SOL Solana")
        assert result["tweet_count"] == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_returns_total_engagement(
        self,
    ) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.search_mentions(query="$SOL Solana")
        # likes + retweets: (150+45) + (80+22) = 297
        assert result["total_engagement"] == 297

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_returns_zero_on_empty_results(
        self,
    ) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_EMPTY_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.search_mentions(query="$UNKNOWNTOKEN")
        assert result["tweet_count"] == 0
        assert result["total_engagement"] == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_raises_on_unauthorized(
        self,
    ) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(401)
        )
        with pytest.raises(CollectorError, match="[Uu]nauthorized|[Ii]nvalid|401"):
            async with TwitterCollector(bearer_token="bad-token") as collector:
                await collector.search_mentions(query="$SOL")

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_search_mentions_raises_on_rate_limit(
        self,
    ) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(429)
        )
        with pytest.raises(CollectorError, match="rate limit"):
            async with TwitterCollector(bearer_token="test-token") as collector:
                await collector.search_mentions(query="$SOL")


class TestTwitterCollectorCollect:
    """TwitterCollector.collect() fetches mention metrics for a list of symbols."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_collect_returns_list(self) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.collect(symbols=["SOL"])
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_collect_returns_symbol_field(self) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.collect(symbols=["SOL"])
        assert result[0]["symbol"] == "SOL"

    @pytest.mark.asyncio
    @respx.mock
    async def test_twitter_collector_collect_single_returns_dict(self) -> None:
        respx.get(f"{TWITTER_BASE_URL}/tweets/search/recent").mock(
            return_value=httpx.Response(200, json=TWITTER_SEARCH_RESPONSE)
        )
        async with TwitterCollector(bearer_token="test-token") as collector:
            result = await collector.collect_single(symbol="SOL")
        assert isinstance(result, dict)
        assert result["symbol"] == "SOL"
