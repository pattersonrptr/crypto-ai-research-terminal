"""TDD tests for scheduler/jobs.py — daily_collection_job + pipeline hardening."""

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


def _make_collector_mock(
    *,
    collect_return: list[dict[str, object]] | None = None,
    collect_side_effect: Exception | None = None,
) -> tuple[MagicMock, MagicMock]:
    """Return (collector_cls_mock, collector_instance_mock) wired for ``async with``.

    The returned ``collector_cls_mock`` can be used as the patch target for
    ``CoinGeckoCollector``.  The instance mock is configured so that
    ``async with CoinGeckoCollector() as c:`` yields the instance with
    ``.collect`` pre-configured.
    """
    instance = MagicMock()
    if collect_side_effect is not None:
        instance.collect = AsyncMock(side_effect=collect_side_effect)
    else:
        instance.collect = AsyncMock(return_value=collect_return or [_RAW])
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)

    cls_mock = MagicMock(return_value=instance)
    return cls_mock, instance


class TestDailyCollectionJob:
    """Tests for daily_collection_job()."""

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_collector(self) -> None:
        """daily_collection_job must call CoinGeckoCollector.collect()."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        cls_mock, instance = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor"),
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            await daily_collection_job()

        instance.collect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_market_processor(self) -> None:
        """daily_collection_job must call MarketProcessor.process() for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        cls_mock, _ = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            await daily_collection_job()

        mock_processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_fundamental_scorer(self) -> None:
        """daily_collection_job must call FundamentalScorer.score() for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        cls_mock, _ = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            await daily_collection_job()

        mock_scorer.score.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_opportunity_engine(self) -> None:
        """daily_collection_job must call full_composite_score for each token."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415
        from app.scoring.heuristic_sub_scorer import SubScoreResult

        sub = SubScoreResult(
            technology_score=0.5,
            tokenomics_score=0.5,
            adoption_score=0.5,
            dev_activity_score=0.5,
            narrative_score=0.6,
            growth_score=0.7,
            risk_score=0.4,
            listing_probability=0.3,
            cycle_leader_prob=0.1,
        )
        cls_mock, _ = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.HeuristicSubScorer") as mock_sub,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_engine,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            mock_sub.score = MagicMock(return_value=sub)
            mock_engine.full_composite_score = MagicMock(return_value=0.75)
            await daily_collection_job()

        mock_engine.full_composite_score.assert_called_once_with(
            fundamental=0.75,
            growth=sub.growth_score,
            narrative=sub.narrative_score,
            listing=sub.listing_probability,
            risk=sub.risk_score,
            cycle_leader_prob=sub.cycle_leader_prob,
        )

    @pytest.mark.asyncio
    async def test_daily_collection_job_calls_persist(self) -> None:
        """daily_collection_job must call _persist_results with the scored results."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415
        from app.scoring.heuristic_sub_scorer import SubScoreResult

        sub = SubScoreResult(
            technology_score=0.5,
            tokenomics_score=0.5,
            adoption_score=0.5,
            dev_activity_score=0.5,
            narrative_score=0.6,
            growth_score=0.7,
            risk_score=0.4,
            listing_probability=0.3,
            cycle_leader_prob=0.1,
        )
        cls_mock, _ = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_processor,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_scorer,
            patch("app.scheduler.jobs.HeuristicSubScorer") as mock_sub,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_engine,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
        ):
            mock_processor.process = MagicMock(return_value=_PROCESSED)
            mock_scorer.score = MagicMock(return_value=0.75)
            mock_sub.score = MagicMock(return_value=sub)
            mock_engine.full_composite_score = MagicMock(return_value=0.82)
            await daily_collection_job()

        mock_persist.assert_awaited_once()
        call_args = mock_persist.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["symbol"] == "BTC"
        assert call_args[0]["fundamental_score"] == 0.75
        assert call_args[0]["opportunity_score"] == 0.82
        assert call_args[0]["growth_score"] == 0.7
        assert call_args[0]["narrative_score"] == 0.6

    @pytest.mark.asyncio
    async def test_daily_collection_job_uses_collector_as_context_manager(
        self,
    ) -> None:
        """daily_collection_job must use CoinGeckoCollector as async context manager."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        cls_mock, instance = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor"),
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
        ):
            await daily_collection_job()

        # Collector is used as context manager at least once (market data);
        # a second usage may occur for category fetching.
        assert instance.__aenter__.await_count >= 1
        assert instance.__aexit__.await_count >= 1


# ---------------------------------------------------------------------------
# Job health monitoring tests
# ---------------------------------------------------------------------------


class TestJobHealthMonitor:
    """Tests for job health recording and dead-letter queue."""

    @pytest.mark.asyncio
    async def test_record_job_success_stores_status_in_redis(self) -> None:
        """record_job_success() must store job status 'success' in Redis."""
        from app.scheduler.jobs import record_job_success  # noqa: PLC0415

        mock_redis = AsyncMock()
        await record_job_success(redis=mock_redis, job_name="daily_collection_job")
        mock_redis.hset.assert_awaited()

    @pytest.mark.asyncio
    async def test_record_job_failure_stores_status_in_redis(self) -> None:
        """record_job_failure() must store job status 'failure' and push to DLQ."""
        from app.scheduler.jobs import record_job_failure  # noqa: PLC0415

        mock_redis = AsyncMock()
        await record_job_failure(
            redis=mock_redis,
            job_name="daily_collection_job",
            error="Connection timeout",
        )
        mock_redis.hset.assert_awaited()
        mock_redis.rpush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_job_status_returns_dict(self) -> None:
        """get_job_status() must return a dict with job health info from Redis."""
        from app.scheduler.jobs import get_job_status  # noqa: PLC0415

        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            b"last_run": b"2025-01-01T06:00:00",
            b"last_status": b"success",
            b"error_count": b"0",
        }
        result = await get_job_status(redis=mock_redis, job_name="daily_collection_job")
        assert isinstance(result, dict)
        assert "last_run" in result
        assert "last_status" in result

    @pytest.mark.asyncio
    async def test_get_job_status_returns_none_fields_when_job_never_ran(
        self,
    ) -> None:
        """get_job_status() returns None fields when job has no Redis entry."""
        from app.scheduler.jobs import get_job_status  # noqa: PLC0415

        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {}
        result = await get_job_status(redis=mock_redis, job_name="never_ran_job")
        assert result["last_run"] is None
        assert result["last_status"] is None

    @pytest.mark.asyncio
    async def test_daily_collection_job_records_success_on_completion(self) -> None:
        """daily_collection_job must call record_job_success on successful run."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        mock_redis = AsyncMock()
        cls_mock, _ = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor"),
            patch("app.scheduler.jobs.FundamentalScorer"),
            patch("app.scheduler.jobs.OpportunityEngine"),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch("app.scheduler.jobs.record_job_success", new_callable=AsyncMock) as mock_rec,
        ):
            await daily_collection_job(redis=mock_redis)

        mock_rec.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_daily_collection_job_records_failure_on_exception(self) -> None:
        """daily_collection_job must call record_job_failure when collect raises."""
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        mock_redis = AsyncMock()
        cls_mock, _ = _make_collector_mock(collect_side_effect=Exception("network error"))
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch("app.scheduler.jobs.record_job_failure", new_callable=AsyncMock) as mock_fail,
        ):
            await daily_collection_job(redis=mock_redis)

        mock_fail.assert_awaited_once()
