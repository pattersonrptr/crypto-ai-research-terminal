"""TDD tests for category population from CoinGecko in the pipeline.

Phase 15: The pipeline must fetch CoinGecko categories for ALL tokens,
pass them to TokenCategoryClassifier.classify(), and persist the result
to Token.category — overwriting stale values on every run.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.token import Token
from app.scoring.pipeline_scorer import PipelineScorerResult
from tests.conftest_helpers import create_sqlite_tables

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_engine():  # type: ignore[return]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(create_sqlite_tables)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):  # type: ignore[return]
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------

_RAW_ETH = {
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

_RAW_UNI = {
    "coingecko_id": "uniswap",
    "symbol": "UNI",
    "name": "Uniswap",
    "price_usd": 10.0,
    "market_cap_usd": 6_000_000_000.0,
    "volume_24h_usd": 200_000_000.0,
    "rank": 30,
    "ath_usd": 45.0,
    "circulating_supply": 600_000_000.0,
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
    categories_return: dict[str, list[str]] | None = None,
) -> MagicMock:
    instance = MagicMock()
    instance.collect = AsyncMock(return_value=collect_return or [_RAW_ETH])
    instance.collect_categories = AsyncMock(
        return_value=categories_return or {},
    )
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=instance)


# ---------------------------------------------------------------------------
# Tests: categories merged into pipeline before scoring
# ---------------------------------------------------------------------------


class TestPipelineCategoriesFromCoingecko:
    """Pipeline must fetch CoinGecko categories and merge them into processed data."""

    @pytest.mark.asyncio
    async def test_pipeline_passes_coingecko_categories_to_classifier(self) -> None:
        """When CoinGecko categories are available, they must be passed to the scorer."""
        from app.scheduler.jobs import daily_collection_job

        categories_map = {"ethereum": ["Smart Contract Platform", "Layer 1 (L1)"]}
        cls_mock = _make_collector_mock(
            collect_return=[_RAW_ETH],
            categories_return=categories_map,
        )

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
            patch(
                "app.scheduler.jobs.detect_cycle_phase", new_callable=AsyncMock, return_value=None
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):

            def capture_process(raw: dict) -> dict:
                result = {
                    **raw,
                    "volume_mcap_ratio": 0.04,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 37.5,
                }
                return result

            mock_proc.process = MagicMock(side_effect=capture_process)
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)

            await daily_collection_job()

        # The persisted result should have token_category=l1 (from CoinGecko categories)
        results = mock_persist.call_args[0][0]
        assert len(results) == 1
        assert results[0]["token_category"] == "l1"

    @pytest.mark.asyncio
    async def test_pipeline_fetches_categories_for_all_tokens(self) -> None:
        """collect_categories must be called with ALL coingecko_ids, not just top 20."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock(
            collect_return=[_RAW_ETH, _RAW_UNI],
            categories_return={
                "ethereum": ["Layer 1 (L1)"],
                "uniswap": ["Decentralized Finance (DeFi)"],
            },
        )

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.detect_cycle_phase", new_callable=AsyncMock, return_value=None
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):
            mock_proc.process = MagicMock(
                side_effect=lambda raw: {
                    **raw,
                    "volume_mcap_ratio": 0.04,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 37.5,
                }
            )
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)

            await daily_collection_job()

        # collect_categories should have been called with ALL ids
        instance = cls_mock.return_value
        call_args = instance.collect_categories.call_args
        coingecko_ids = call_args[0][0]
        assert "ethereum" in coingecko_ids
        assert "uniswap" in coingecko_ids

    @pytest.mark.asyncio
    async def test_pipeline_classifies_defi_from_coingecko_categories(self) -> None:
        """UNI with DeFi categories from CoinGecko must be classified as 'defi'."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock(
            collect_return=[_RAW_UNI],
            categories_return={"uniswap": ["Decentralized Finance (DeFi)", "Ethereum Ecosystem"]},
        )

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
            patch(
                "app.scheduler.jobs.detect_cycle_phase", new_callable=AsyncMock, return_value=None
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):
            mock_proc.process = MagicMock(
                side_effect=lambda raw: {
                    **raw,
                    "volume_mcap_ratio": 0.03,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 77.0,
                }
            )
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.60)
            mock_eng.full_composite_score = MagicMock(return_value=0.70)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.70)

            await daily_collection_job()

        results = mock_persist.call_args[0][0]
        assert results[0]["token_category"] == "defi"

    @pytest.mark.asyncio
    async def test_pipeline_category_collection_failure_uses_fallback(self) -> None:
        """If collect_categories fails, classification falls back to symbol-based."""
        from app.scheduler.jobs import daily_collection_job

        cls_mock = _make_collector_mock(collect_return=[_RAW_ETH])
        # Make collect_categories raise — simulates CoinGecko being down
        cls_mock.return_value.collect_categories = AsyncMock(side_effect=Exception("rate limited"))

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector", cls_mock),
            patch("app.scheduler.jobs.MarketProcessor") as mock_proc,
            patch("app.scheduler.jobs.PipelineScorer") as mock_pipe,
            patch("app.scheduler.jobs.FundamentalScorer") as mock_fund,
            patch("app.scheduler.jobs.OpportunityEngine") as mock_eng,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock) as mock_persist,
            patch(
                "app.scheduler.jobs.detect_cycle_phase", new_callable=AsyncMock, return_value=None
            ),
            patch(
                "app.scheduler.jobs.get_active_weights",
                new_callable=AsyncMock,
                side_effect=Exception("no DB"),
            ),
        ):
            mock_proc.process = MagicMock(
                side_effect=lambda raw: {
                    **raw,
                    "volume_mcap_ratio": 0.04,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 37.5,
                }
            )
            mock_pipe.score = MagicMock(return_value=_SUB_SCORES)
            mock_fund.sub_pillar_score = MagicMock(return_value=0.75)
            mock_eng.full_composite_score = MagicMock(return_value=0.80)
            mock_eng.cycle_adjusted_score = MagicMock(return_value=0.80)

            await daily_collection_job()

        # Should still succeed with symbol-based fallback
        results = mock_persist.call_args[0][0]
        assert len(results) == 1
        # ETH without CoinGecko cats → unknown (symbol not in memecoin list)
        assert results[0]["token_category"] == "unknown"


# ---------------------------------------------------------------------------
# Tests: _persist_results always updates category
# ---------------------------------------------------------------------------


class TestPersistResultsUpdatesCategory:
    """_persist_results must always update token.category, even when it already has one."""

    @pytest.mark.asyncio
    async def test_persist_results_overwrites_existing_category(
        self, async_session: AsyncSession
    ) -> None:
        """A token initially classified as 'unknown' should be updated to 'l1'."""
        from app.scheduler.jobs import _persist_results

        result_unknown: dict[str, object] = {
            "coingecko_id": "ethereum",
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": 3000.0,
            "market_cap_usd": 350_000_000_000.0,
            "volume_24h_usd": 15_000_000_000.0,
            "rank": 2,
            "token_category": "unknown",
        }

        # First run: classified as unknown
        await _persist_results([result_unknown], session=async_session)
        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category == "unknown"

        # Second run: now we have real CoinGecko categories → l1
        result_l1 = {**result_unknown, "token_category": "l1"}
        await _persist_results([result_l1], session=async_session)
        await async_session.refresh(token)
        assert token.category == "l1"

    @pytest.mark.asyncio
    async def test_persist_results_does_not_downgrade_to_unknown(
        self, async_session: AsyncSession
    ) -> None:
        """If token already has a real category, don't overwrite with 'unknown'."""
        from app.scheduler.jobs import _persist_results

        result_l1: dict[str, object] = {
            "coingecko_id": "ethereum",
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": 3000.0,
            "market_cap_usd": 350_000_000_000.0,
            "volume_24h_usd": 15_000_000_000.0,
            "rank": 2,
            "token_category": "l1",
        }

        # First run: l1
        await _persist_results([result_l1], session=async_session)

        # Second run: category detection failed → unknown
        result_unknown = {**result_l1, "token_category": "unknown"}
        await _persist_results([result_unknown], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        # Should NOT downgrade from l1 to unknown
        assert token.category == "l1"

    @pytest.mark.asyncio
    async def test_persist_results_updates_from_one_real_category_to_another(
        self, async_session: AsyncSession
    ) -> None:
        """If CoinGecko reclassifies a token, update accordingly."""
        from app.scheduler.jobs import _persist_results

        result: dict[str, object] = {
            "coingecko_id": "some-token",
            "symbol": "TKN",
            "name": "SomeToken",
            "price_usd": 1.0,
            "market_cap_usd": 1_000_000.0,
            "volume_24h_usd": 100_000.0,
            "rank": 100,
            "token_category": "infrastructure",
        }

        await _persist_results([result], session=async_session)

        # CoinGecko reclassifies as AI
        result_ai = {**result, "token_category": "ai"}
        await _persist_results([result_ai], session=async_session)

        token = (await async_session.execute(select(Token))).scalars().first()
        assert token is not None
        assert token.category == "ai"
