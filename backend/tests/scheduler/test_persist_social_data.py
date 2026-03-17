"""TDD tests for social data persistence into the social_data table.

Item 2 of Ranking Quality Loop: persist Reddit + Twitter data so
PipelineScorer uses real signals instead of heuristic fallbacks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_data import SocialData
from app.models.token import Token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(token_id: int, symbol: str) -> Token:
    """Create a minimal Token stub for tests."""
    token = Token()
    token.id = token_id
    token.symbol = symbol
    token.name = f"{symbol} Token"
    token.coingecko_id = symbol.lower()
    token.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    return token


def _make_reddit_data(
    *,
    subscribers: int = 500_000,
    posts_24h: int = 50,
    avg_score: float = 25.0,
) -> dict[str, Any]:
    """Create mock Reddit collector output."""
    return {
        "subreddit": "Bitcoin",
        "subscribers": subscribers,
        "active_users": 10_000,
        "posts_24h": posts_24h,
        "avg_score": avg_score,
    }


def _make_twitter_data(
    *,
    mention_count: int = 200,
    total_engagement: int = 5000,
) -> dict[str, Any]:
    """Create mock Twitter collector output."""
    return {
        "symbol": "BTC",
        "mention_count": mention_count,
        "total_engagement": total_engagement,
        "texts": ["Bitcoin to the moon!", "BTC looking bullish"],
    }


# ---------------------------------------------------------------------------
# persist_social_data tests
# ---------------------------------------------------------------------------


class TestPersistSocialData:
    """persist_social_data writes Reddit + Twitter metrics to social_data table."""

    @pytest.mark.asyncio
    async def test_persist_social_data_creates_social_data_row(self) -> None:
        """Must insert a SocialData row for a token with Reddit data."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "BTC")

        # Mock session.execute to return the token
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"BTC": _make_reddit_data()}
        twitter_data: dict[str, dict[str, Any]] = {}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        # Should have called session.add with a SocialData instance
        session.add.assert_called()
        added_obj = session.add.call_args[0][0]
        assert isinstance(added_obj, SocialData)
        assert added_obj.token_id == 1
        assert added_obj.reddit_subscribers == 500_000
        assert added_obj.reddit_posts_24h == 50

    @pytest.mark.asyncio
    async def test_persist_social_data_includes_twitter_metrics(self) -> None:
        """Must include Twitter mentions and engagement when available."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "BTC")

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"BTC": _make_reddit_data()}
        twitter_data = {"BTC": _make_twitter_data(mention_count=300, total_engagement=8000)}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        added_obj = session.add.call_args[0][0]
        assert added_obj.twitter_mentions_24h == 300
        assert added_obj.twitter_engagement == 8000

    @pytest.mark.asyncio
    async def test_persist_social_data_twitter_only(self) -> None:
        """Must persist Twitter data even without Reddit data for a token."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "BTC")

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data: dict[str, dict[str, Any]] = {}
        twitter_data = {"BTC": _make_twitter_data()}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        added_obj = session.add.call_args[0][0]
        assert added_obj.twitter_mentions_24h == 200
        assert added_obj.reddit_subscribers == 0  # default

    @pytest.mark.asyncio
    async def test_persist_social_data_defaults_for_missing_twitter(self) -> None:
        """Twitter fields must default to 0 when only Reddit data is available."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "BTC")

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"BTC": _make_reddit_data()}
        twitter_data: dict[str, dict[str, Any]] = {}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        added_obj = session.add.call_args[0][0]
        assert added_obj.twitter_mentions_24h == 0
        assert added_obj.twitter_engagement == 0

    @pytest.mark.asyncio
    async def test_persist_social_data_skips_unknown_token(self) -> None:
        """Must skip symbols whose token is not in the DB."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None  # Token not found
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"UNKNOWN": _make_reddit_data()}
        twitter_data: dict[str, dict[str, Any]] = {}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_social_data_calls_commit(self) -> None:
        """Must commit the session after persisting all rows."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "BTC")

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"BTC": _make_reddit_data()}
        twitter_data: dict[str, dict[str, Any]] = {}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_persist_social_data_merges_reddit_and_twitter(self) -> None:
        """Must merge Reddit + Twitter data for the same symbol into one row."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)
        token = _make_token(1, "ETH")

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = token
        session.execute = AsyncMock(return_value=result_mock)

        reddit_data = {"ETH": _make_reddit_data(subscribers=2_000_000, posts_24h=120)}
        twitter_data = {"ETH": _make_twitter_data(mention_count=500, total_engagement=12_000)}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        added_obj = session.add.call_args[0][0]
        assert added_obj.reddit_subscribers == 2_000_000
        assert added_obj.reddit_posts_24h == 120
        assert added_obj.twitter_mentions_24h == 500
        assert added_obj.twitter_engagement == 12_000

    @pytest.mark.asyncio
    async def test_persist_social_data_multiple_symbols(self) -> None:
        """Must persist data for multiple symbols in a single call."""
        from app.scheduler.jobs import persist_social_data

        session = AsyncMock(spec=AsyncSession)

        # Different tokens per call
        tokens = {"BTC": _make_token(1, "BTC"), "ETH": _make_token(2, "ETH")}

        def _select_side_effect(*_args: Any, **_kwargs: Any) -> MagicMock:
            result = MagicMock()
            # Will be called for BTC first, then ETH
            result.scalars.return_value.first.side_effect = [tokens["BTC"], tokens["ETH"]]
            return result

        session.execute = AsyncMock(side_effect=_select_side_effect)

        reddit_data = {
            "BTC": _make_reddit_data(subscribers=5_000_000),
            "ETH": _make_reddit_data(subscribers=2_000_000),
        }
        twitter_data: dict[str, dict[str, Any]] = {}

        await persist_social_data(
            reddit_data=reddit_data,
            twitter_data=twitter_data,
            session=session,
        )

        assert session.add.call_count == 2


# ---------------------------------------------------------------------------
# collect_twitter_data helper tests
# ---------------------------------------------------------------------------


class TestCollectTwitterData:
    """collect_twitter_data orchestrates TwitterTwikitCollector for all symbols."""

    @pytest.mark.asyncio
    async def test_collect_twitter_data_calls_collector(self) -> None:
        """Must call collect_mentions for each symbol."""
        from app.scheduler.jobs import collect_twitter_data

        mock_collector = AsyncMock()
        mock_collector.collect_mentions.return_value = _make_twitter_data()

        result = await collect_twitter_data(
            symbols=["BTC"],
            twitter_collector=mock_collector,
        )

        mock_collector.collect_mentions.assert_awaited_once_with("BTC")
        assert "BTC" in result

    @pytest.mark.asyncio
    async def test_collect_twitter_data_handles_error(self) -> None:
        """Must skip a symbol on collector error without crashing."""
        from app.scheduler.jobs import collect_twitter_data

        mock_collector = AsyncMock()
        mock_collector.collect_mentions.side_effect = Exception("Twitter down")

        result = await collect_twitter_data(
            symbols=["BTC"],
            twitter_collector=mock_collector,
        )

        assert "BTC" not in result

    @pytest.mark.asyncio
    async def test_collect_twitter_data_multiple_symbols(self) -> None:
        """Must collect data for each symbol independently."""
        from app.scheduler.jobs import collect_twitter_data

        mock_collector = AsyncMock()
        mock_collector.collect_mentions.side_effect = [
            _make_twitter_data(mention_count=100),
            _make_twitter_data(mention_count=200),
        ]

        result = await collect_twitter_data(
            symbols=["BTC", "ETH"],
            twitter_collector=mock_collector,
        )

        assert len(result) == 2
        assert result["BTC"]["mention_count"] == 100
        assert result["ETH"]["mention_count"] == 200
