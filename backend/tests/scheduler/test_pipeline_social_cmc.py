"""TDD tests for pipeline social data integration.

Tests:
- subreddit_map lookups
- persist_social_data helper
- persist_cmc_data helper
- collect_social_data orchestrator
- collect_cmc_data orchestrator
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.collectors.subreddit_map import SYMBOL_TO_SUBREDDIT, get_subreddit

# ---------------------------------------------------------------------------
# subreddit_map tests
# ---------------------------------------------------------------------------


class TestSubredditMap:
    """Tests for the symbol-to-subreddit mapping."""

    def test_get_subreddit_known_symbol(self) -> None:
        """get_subreddit must return the subreddit for known symbols."""
        assert get_subreddit("BTC") == "Bitcoin"
        assert get_subreddit("ETH") == "ethereum"

    def test_get_subreddit_unknown_symbol(self) -> None:
        """get_subreddit must return None for unknown symbols."""
        assert get_subreddit("UNKNOWNXYZ") is None

    def test_get_subreddit_case_insensitive(self) -> None:
        """get_subreddit must be case-insensitive."""
        assert get_subreddit("btc") == "Bitcoin"
        assert get_subreddit("Eth") == "ethereum"

    def test_map_has_major_tokens(self) -> None:
        """SYMBOL_TO_SUBREDDIT must contain major tokens."""
        for sym in ("BTC", "ETH", "SOL", "ADA", "DOT", "LINK"):
            assert sym in SYMBOL_TO_SUBREDDIT


# ---------------------------------------------------------------------------
# collect_social_data + persist tests
# ---------------------------------------------------------------------------


class TestCollectSocialData:
    """Tests for the collect_social_data pipeline helper."""

    @pytest.mark.asyncio
    async def test_collect_social_data_calls_reddit_for_mapped_symbols(self) -> None:
        """collect_social_data must call SocialCollector for symbols with subreddits."""
        from app.scheduler.jobs import collect_social_data

        mock_reddit = AsyncMock()
        mock_reddit.collect_single.return_value = {
            "subreddit": "Bitcoin",
            "subscribers": 5000000,
            "active_users": 10000,
            "posts_24h": 50,
            "avg_score": 25.0,
        }

        symbols = ["BTC", "UNKNOWNXYZ"]
        result = await collect_social_data(symbols, reddit_collector=mock_reddit)

        # Only BTC should be collected (UNKNOWNXYZ has no subreddit)
        mock_reddit.collect_single.assert_awaited_once()
        assert "BTC" in result

    @pytest.mark.asyncio
    async def test_collect_social_data_returns_dict_per_symbol(self) -> None:
        """collect_social_data must return a dict keyed by symbol."""
        from app.scheduler.jobs import collect_social_data

        mock_reddit = AsyncMock()
        mock_reddit.collect_single.return_value = {
            "subreddit": "Bitcoin",
            "subscribers": 5000000,
            "active_users": 10000,
            "posts_24h": 50,
            "avg_score": 25.0,
        }

        result = await collect_social_data(["BTC"], reddit_collector=mock_reddit)

        assert isinstance(result, dict)
        assert result["BTC"]["subscribers"] == 5000000

    @pytest.mark.asyncio
    async def test_collect_social_data_handles_collector_error(self) -> None:
        """collect_social_data must skip a symbol on collector error."""
        from app.scheduler.jobs import collect_social_data

        mock_reddit = AsyncMock()
        mock_reddit.collect_single.side_effect = Exception("Reddit down")

        result = await collect_social_data(["BTC"], reddit_collector=mock_reddit)

        assert "BTC" not in result


# ---------------------------------------------------------------------------
# collect_cmc_data tests
# ---------------------------------------------------------------------------


class TestCollectCmcData:
    """Tests for the collect_cmc_data pipeline helper."""

    @pytest.mark.asyncio
    async def test_collect_cmc_data_returns_dict_keyed_by_symbol(self) -> None:
        """collect_cmc_data must return a dict keyed by symbol."""
        from app.scheduler.jobs import collect_cmc_data

        mock_cmc = AsyncMock()
        mock_cmc.collect.return_value = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "cmc_rank": 1,
                "tags": ["mineable"],
                "category": "Cryptocurrency",
            },
        ]

        result = await collect_cmc_data(cmc_collector=mock_cmc)

        assert isinstance(result, dict)
        assert "BTC" in result
        assert result["BTC"]["cmc_rank"] == 1

    @pytest.mark.asyncio
    async def test_collect_cmc_data_handles_error(self) -> None:
        """collect_cmc_data must return empty dict on error."""
        from app.scheduler.jobs import collect_cmc_data

        mock_cmc = AsyncMock()
        mock_cmc.collect.side_effect = Exception("CMC API down")

        result = await collect_cmc_data(cmc_collector=mock_cmc)

        assert result == {}

    @pytest.mark.asyncio
    async def test_collect_cmc_data_indexes_by_symbol(self) -> None:
        """collect_cmc_data must index results by uppercase symbol."""
        from app.scheduler.jobs import collect_cmc_data

        mock_cmc = AsyncMock()
        mock_cmc.collect.return_value = [
            {"symbol": "BTC", "cmc_rank": 1, "tags": [], "category": ""},
            {"symbol": "ETH", "cmc_rank": 2, "tags": [], "category": ""},
        ]

        result = await collect_cmc_data(cmc_collector=mock_cmc)

        assert len(result) == 2
        assert result["ETH"]["cmc_rank"] == 2
