"""TDD tests for TwitterTwikitCollector — free Twitter/X scraping via twikit."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.collectors.twitter_twikit_collector import TwitterTwikitCollector


# ---------------------------------------------------------------------------
# Helpers — mock twikit objects
# ---------------------------------------------------------------------------


def _make_tweet(
    text: str = "Check out $BTC!",
    favorite_count: int = 10,
    retweet_count: int = 5,
) -> MagicMock:
    """Return a mock twikit Tweet object."""
    tweet = MagicMock()
    tweet.text = text
    tweet.favorite_count = favorite_count
    tweet.retweet_count = retweet_count
    return tweet


def _make_search_result(tweets: list[MagicMock] | None = None) -> MagicMock:
    """Return a mock search result that is iterable over tweets."""
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter(tweets or []))
    result.__len__ = MagicMock(return_value=len(tweets or []))
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTwitterTwikitCollectorInit:
    """Test collector initialisation."""

    def test_init_stores_credentials(self) -> None:
        """Collector must store username, email, password."""
        collector = TwitterTwikitCollector(
            username="user", email="u@e.com", password="pass"
        )
        assert collector.username == "user"
        assert collector.email == "u@e.com"
        assert collector.password == "pass"

    def test_init_sets_cookies_path(self) -> None:
        """Collector must default cookies_path to 'twitter_cookies.json'."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p"
        )
        assert collector.cookies_path == "twitter_cookies.json"

    def test_init_custom_cookies_path(self) -> None:
        """Collector must accept a custom cookies_path."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
            cookies_path="/tmp/cookies.json",
        )
        assert collector.cookies_path == "/tmp/cookies.json"


class TestTwitterTwikitCollectorLogin:
    """Test login and cookie persistence."""

    @pytest.mark.asyncio
    async def test_login_loads_cookies_when_file_exists(
        self, tmp_path: Path,
    ) -> None:
        """login() must load cookies from file when it exists."""
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text("{}")

        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
            cookies_path=str(cookies_file),
        )
        mock_client = AsyncMock()
        collector._client = mock_client  # type: ignore[assignment]

        await collector.login()

        mock_client.load_cookies.assert_called_once_with(str(cookies_file))

    @pytest.mark.asyncio
    async def test_login_performs_fresh_login_when_no_cookies(
        self, tmp_path: Path,
    ) -> None:
        """login() must call client.login when cookies file does not exist."""
        cookies_file = tmp_path / "cookies.json"

        collector = TwitterTwikitCollector(
            username="user", email="e@e.com", password="pass",
            cookies_path=str(cookies_file),
        )
        mock_client = AsyncMock()
        collector._client = mock_client  # type: ignore[assignment]

        await collector.login()

        mock_client.login.assert_awaited_once_with(
            auth_info_1="user",
            auth_info_2="e@e.com",
            password="pass",
        )

    @pytest.mark.asyncio
    async def test_login_saves_cookies_after_fresh_login(
        self, tmp_path: Path,
    ) -> None:
        """login() must save cookies after a fresh login."""
        cookies_file = tmp_path / "cookies.json"

        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
            cookies_path=str(cookies_file),
        )
        mock_client = AsyncMock()
        collector._client = mock_client  # type: ignore[assignment]

        await collector.login()

        mock_client.save_cookies.assert_called_once_with(str(cookies_file))


class TestTwitterTwikitCollectorCollect:
    """Test mention collection."""

    @pytest.mark.asyncio
    async def test_collect_mentions_returns_dict(self) -> None:
        """collect_mentions must return a dict with expected keys."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        tweets = [_make_tweet("BTC is great!", 20, 5)]
        mock_client.search_tweet.return_value = _make_search_result(tweets)
        collector._client = mock_client  # type: ignore[assignment]

        result = await collector.collect_mentions("BTC")

        assert isinstance(result, dict)
        assert "symbol" in result
        assert "mention_count" in result
        assert "total_engagement" in result

    @pytest.mark.asyncio
    async def test_collect_mentions_counts_tweets(self) -> None:
        """collect_mentions must set mention_count to number of tweets found."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        tweets = [_make_tweet() for _ in range(3)]
        mock_client.search_tweet.return_value = _make_search_result(tweets)
        collector._client = mock_client  # type: ignore[assignment]

        result = await collector.collect_mentions("ETH")

        assert result["mention_count"] == 3

    @pytest.mark.asyncio
    async def test_collect_mentions_sums_engagement(self) -> None:
        """collect_mentions must sum likes+retweets as total_engagement."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        tweets = [
            _make_tweet(favorite_count=10, retweet_count=5),
            _make_tweet(favorite_count=20, retweet_count=10),
        ]
        mock_client.search_tweet.return_value = _make_search_result(tweets)
        collector._client = mock_client  # type: ignore[assignment]

        result = await collector.collect_mentions("SOL")

        assert result["total_engagement"] == 45  # (10+5) + (20+10)

    @pytest.mark.asyncio
    async def test_collect_mentions_returns_raw_texts(self) -> None:
        """collect_mentions must include raw tweet texts for sentiment analysis."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        tweets = [_make_tweet(text="BTC to the moon!")]
        mock_client.search_tweet.return_value = _make_search_result(tweets)
        collector._client = mock_client  # type: ignore[assignment]

        result = await collector.collect_mentions("BTC")

        assert "texts" in result
        assert "BTC to the moon!" in result["texts"]

    @pytest.mark.asyncio
    async def test_collect_mentions_handles_empty_results(self) -> None:
        """collect_mentions must handle zero results gracefully."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        mock_client.search_tweet.return_value = _make_search_result([])
        collector._client = mock_client  # type: ignore[assignment]

        result = await collector.collect_mentions("RARE")

        assert result["mention_count"] == 0
        assert result["total_engagement"] == 0
        assert result["texts"] == []

    @pytest.mark.asyncio
    async def test_collect_mentions_searches_dollar_symbol(self) -> None:
        """collect_mentions must search for $SYMBOL."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        mock_client = AsyncMock()
        mock_client.search_tweet.return_value = _make_search_result([])
        collector._client = mock_client  # type: ignore[assignment]

        await collector.collect_mentions("BTC")

        call_args = mock_client.search_tweet.call_args
        query = call_args[0][0] if call_args[0] else call_args[1].get("query", "")
        assert "$BTC" in query

    @pytest.mark.asyncio
    async def test_collect_calls_collect_mentions_per_symbol(self) -> None:
        """collect() must call collect_mentions for each symbol."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        collector.collect_mentions = AsyncMock(  # type: ignore[assignment]
            return_value={"symbol": "BTC", "mention_count": 1, "total_engagement": 5, "texts": []}
        )

        results = await collector.collect(["BTC", "ETH"])

        assert len(results) == 2
        assert collector.collect_mentions.await_count == 2

    @pytest.mark.asyncio
    async def test_collect_single_returns_one_result(self) -> None:
        """collect_single() must return a single dict."""
        collector = TwitterTwikitCollector(
            username="u", email="e@e.com", password="p",
        )
        collector.collect_mentions = AsyncMock(  # type: ignore[assignment]
            return_value={"symbol": "BTC", "mention_count": 1, "total_engagement": 5, "texts": []}
        )

        result = await collector.collect_single("BTC")

        assert result["symbol"] == "BTC"
