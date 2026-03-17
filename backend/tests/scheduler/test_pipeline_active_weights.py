"""TDD tests for wiring active weights into the daily pipeline.

The daily_collection_job must load active weights from the DB/cache via
``get_active_weights()`` and pass them to ``OpportunityEngine.full_composite_score()``.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scoring.pipeline_scorer import PipelineScorerResult

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

_SUB_SCORES = PipelineScorerResult(
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

_CALIBRATED_WEIGHTS: dict[str, object] = {
    "fundamental": 0.25,
    "growth": 0.20,
    "narrative": 0.15,
    "listing": 0.10,
    "risk": 0.30,
    "source": "calibrated",
}


def _make_collector_mock(
    *,
    collect_return: list[dict[str, object]] | None = None,
) -> MagicMock:
    """Return a CoinGeckoCollector class mock wired for ``async with``."""
    instance = MagicMock()
    instance.collect = AsyncMock(return_value=collect_return or [_RAW])
    instance.collect_categories = AsyncMock(return_value={})
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=instance)


class TestPipelineActiveWeights:
    """daily_collection_job must use DB-loaded weights for scoring."""

    @pytest.mark.asyncio
    async def test_pipeline_calls_get_active_weights(self) -> None:
        """Pipeline must call get_active_weights() once before scoring."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.detect_cycle_phase",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                return_value=_CALIBRATED_WEIGHTS,
            ) as mock_get_weights,
        ):
            mock_proc.process = MagicMock(return_value=_PROCESSED)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)
            await daily_collection_job()

        mock_get_weights.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pipeline_passes_weights_to_full_composite_score(self) -> None:
        """full_composite_score must receive ``weights`` kwarg from DB."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.detect_cycle_phase",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                return_value=_CALIBRATED_WEIGHTS,
            ),
        ):
            mock_proc.process = MagicMock(return_value=_PROCESSED)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)
            await daily_collection_job()

        mock_eng.full_composite_score.assert_called_once_with(
            fundamental=0.75,
            growth=_SUB_SCORES.growth_score,
            narrative=_SUB_SCORES.narrative_score,
            listing=_SUB_SCORES.listing_probability,
            risk=_SUB_SCORES.risk_score,
            cycle_leader_prob=_SUB_SCORES.cycle_leader_prob,
            weights={
                "fundamental": 0.25,
                "growth": 0.20,
                "narrative": 0.15,
                "listing": 0.10,
                "risk": 0.30,
            },
        )

    @pytest.mark.asyncio
    async def test_pipeline_uses_defaults_when_get_active_weights_fails(self) -> None:
        """If get_active_weights raises, pipeline should fall back to no weights (defaults)."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock()
        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.detect_cycle_phase",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("DB down"),
            ),
        ):
            mock_proc.process = MagicMock(return_value=_PROCESSED)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)
            await daily_collection_job()

        # Should still be called — but without custom weights (fallback to defaults)
        mock_eng.full_composite_score.assert_called_once()
        call_kwargs = mock_eng.full_composite_score.call_args
        # weights should be None (defaults) when get_active_weights fails
        assert call_kwargs.kwargs.get("weights") is None or "weights" not in call_kwargs.kwargs
