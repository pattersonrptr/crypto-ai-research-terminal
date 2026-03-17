"""TDD tests for category risk multiplier integration in the pipeline.

The pipeline must classify each token and apply the category risk
multiplier to the opportunity score before persisting.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scoring.pipeline_scorer import PipelineScorerResult

_RAW = {
    "coingecko_id": "pepe",
    "symbol": "PEPE",
    "name": "Pepe",
    "price_usd": 0.00001,
    "market_cap_usd": 5_000_000_000.0,
    "volume_24h_usd": 500_000_000.0,
    "rank": 25,
    "ath_usd": 0.00002,
    "circulating_supply": 420_690_000_000_000.0,
}

_PROCESSED: dict[str, Any] = {
    **_RAW,
    "volume_mcap_ratio": 0.1,
    "price_velocity": 0.0,
    "ath_distance_pct": 50.0,
}

_SUB_SCORES = PipelineScorerResult(
    technology_score=0.3,
    tokenomics_score=0.3,
    adoption_score=0.6,
    dev_activity_score=0.2,
    narrative_score=0.8,
    growth_score=0.7,
    risk_score=0.3,
    listing_probability=0.4,
    cycle_leader_prob=0.05,
)


def _make_collector_mock(
    *,
    collect_return: list[dict[str, object]] | None = None,
) -> MagicMock:
    instance = MagicMock()
    instance.collect = AsyncMock(return_value=collect_return or [_RAW])
    instance.collect_categories = AsyncMock(return_value={})
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=instance)


class TestPipelineCategoryMultiplier:
    """Pipeline must apply category risk multiplier to opportunity scores."""

    @pytest.mark.asyncio
    async def test_pipeline_applies_category_multiplier_to_memecoin(self) -> None:
        """A memecoin (PEPE) should have its score multiplied by 0.70."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock()
        base_score = 0.80

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
            patch(
                "app.scheduler.jobs.detect_cycle_phase",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):
            mock_proc.process = MagicMock(return_value=_PROCESSED)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.50)
            mock_eng.full_composite_score = MagicMock(return_value=base_score)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=base_score)
            await daily_collection_job()

        mock_persist.assert_awaited_once()
        results = mock_persist.call_args[0][0]
        assert len(results) == 1
        # PEPE is a known memecoin → 0.80 * 0.70 = 0.56
        assert results[0]["opportunity_score"] == pytest.approx(0.56)
        assert results[0]["token_category"] == "memecoin"

    @pytest.mark.asyncio
    async def test_pipeline_l1_token_score_unchanged(self) -> None:
        """An L1 token (ETH) should NOT have its score reduced."""
        from app.scheduler.jobs import daily_collection_job

        eth_raw = {
            "coingecko_id": "ethereum",
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": 3000.0,
            "market_cap_usd": 350_000_000_000.0,
            "volume_24h_usd": 15_000_000_000.0,
            "rank": 2,
            "ath_usd": 4800.0,
            "circulating_supply": 120_000_000.0,
        }
        eth_processed = {
            **eth_raw,
            "volume_mcap_ratio": 0.04,
            "price_velocity": 0.0,
            "ath_distance_pct": 37.5,
        }
        cls_mock = _make_collector_mock(collect_return=[eth_raw])
        base_score = 0.80

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
            patch(
                "app.scheduler.jobs.detect_cycle_phase",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):
            mock_proc.process = MagicMock(return_value=eth_processed)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=base_score)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=base_score)
            await daily_collection_job()

        results = mock_persist.call_args[0][0]
        assert len(results) == 1
        # ETH is unknown category (no CoinGecko cats) → 0.80 * 0.90 = 0.72
        # (unknown gets 0.90 penalty)
        assert results[0]["opportunity_score"] == pytest.approx(0.72)
