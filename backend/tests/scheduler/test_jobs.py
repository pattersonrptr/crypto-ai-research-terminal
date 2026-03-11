"""TDD tests for scheduler/jobs.py — daily_collection_job."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_RAW = {
    "coingecko_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "price_usd": 60000.0,
    "market_cap_usd": 1_200_000_000_000.0,
    "volume_24h_usd": 30_000_000_000.0,
    "rank": 1,
    "ath_usd": 73000.0,
    "circulating_supply": 19_000_000.0,
}
_PROCESSED = {
    **_RAW,
    "volume_mcap_ratio": 0.025,
    "price_velocity": 0.0,
    "ath_distance_pct": 17.8,
}


class TestDailyCollectionJob:
    """Tests for daily_collection_job()."""

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_collector(self) -> None:
        """daily_collection_job must call CoinGeckoCollector.collect()."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch("app.scheduler.jobs.MarketProcessor"),
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            collector_instance = mock_collector_cls.return_value
            collector_instance.collect = AsyncMock(return_value=[_RAW])
            await daily_collection_job()

        collector_instance.collect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_market_processor(self) -> None:
        """daily_collection_job must call MarketProcessor.process() for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_collector_cls.return_value.collect = AsyncMock(return_value=[_RAW])
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            await daily_collection_job()

        mock_processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_fundamental_scorer(self) -> None:
        """daily_collection_job must call FundamentalScorer.score() for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_collector_cls.return_value.collect = AsyncMock(return_value=[_RAW])
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            await daily_collection_job()

        mock_scorer.score.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_opportunity_engine(self) -> None:
        """daily_collection_job must call OpportunityEngine.composite_score() for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_engine,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_collector_cls.return_value.collect = AsyncMock(return_value=[_RAW])
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            mock_engine.composite_score = MagicMock(return_value=0.75)
            await daily_collection_job()

        mock_engine.composite_score.assert_called_once_with(0.75)

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_persist(self) -> None:
        """daily_collection_job must call _persist_results with the scored results."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_engine,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
        ):
            mock_collector_cls.return_value.collect = AsyncMock(return_value=[_RAW])
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            mock_engine.composite_score = MagicMock(return_value=0.75)
            await daily_collection_job()

        mock_persist.assert_awaited_once()
        call_args = mock_persist.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["symbol"] == "BTC"
        assert call_args[0]["fundamental_score"] == 0.75
        assert call_args[0]["opportunity_score"] == 0.75

