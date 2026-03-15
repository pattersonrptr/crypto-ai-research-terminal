"""Tests for narrative snapshot integration in the daily collection pipeline.

Verifies that daily_collection_job calls build_narrative_snapshot_from_categories
and persist_narrative_snapshot after scoring.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.narrative import NarrativeCluster


def _make_raw_token(symbol: str, categories: list[str] | None = None) -> dict[str, Any]:
    """Create a minimal CoinGecko-like token dict for testing."""
    return {
        "symbol": symbol,
        "name": f"{symbol} Token",
        "coingecko_id": symbol.lower(),
        "market_cap_usd": 1_000_000_000,
        "volume_24h_usd": 50_000_000,
        "price_usd": 100.0,
        "rank": 10,
        "ath_usd": 200.0,
        "circulating_supply": 10_000_000,
        "price_change_24h_pct": 2.0,
        "price_change_7d_pct": 5.0,
        "categories": categories or [],
    }


class TestPipelineNarrativeIntegration:
    """daily_collection_job builds + persists narrative snapshots."""

    @pytest.mark.asyncio
    async def test_daily_job_calls_narrative_snapshot(self) -> None:
        """Pipeline should build narrative clusters from collected token data."""
        raw_tokens = [
            _make_raw_token("FET", categories=["ai"]),
            _make_raw_token("RNDR", categories=["ai"]),
            _make_raw_token("AAVE", categories=["defi"]),
            _make_raw_token("COMP", categories=["defi"]),
        ]

        # Categories returned by collect_categories (keyed by coingecko_id)
        fake_categories = {
            "fet": ["ai"],
            "rndr": ["ai"],
            "aave": ["defi"],
            "comp": ["defi"],
        }

        mock_clusters = [MagicMock(spec=NarrativeCluster)]

        with (
            patch(
                "app.scheduler.jobs.CoinGeckoCollector",
            ) as mock_collector_cls,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.build_narrative_snapshot_from_categories",
                return_value=mock_clusters,
            ) as mock_build,
            patch(
                "app.scheduler.jobs.persist_narrative_snapshot",
                new_callable=AsyncMock,
            ) as mock_persist,
        ):
            # Set up collector mock as async context manager
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = raw_tokens
            mock_collector.collect_categories.return_value = fake_categories
            mock_collector_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_collector,
            )
            mock_collector_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.scheduler.jobs import daily_collection_job

            await daily_collection_job(redis=None)

            mock_build.assert_called_once()
            # The first arg should be a list of token data dicts
            call_args = mock_build.call_args[0][0]
            assert len(call_args) == 4

            mock_persist.assert_awaited_once_with(mock_clusters)

    @pytest.mark.asyncio
    async def test_daily_job_narrative_failure_does_not_break_pipeline(self) -> None:
        """If narrative snapshot fails, pipeline should still complete."""
        raw_tokens = [_make_raw_token("BTC")]

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_collector_cls,
            patch(
                "app.scheduler.jobs._persist_results",
                new_callable=AsyncMock,
            ) as mock_persist_results,
            patch(
                "app.scheduler.jobs.build_narrative_snapshot_from_categories",
                side_effect=RuntimeError("narrative failure"),
            ),
            patch(
                "app.scheduler.jobs.persist_narrative_snapshot",
                new_callable=AsyncMock,
            ),
        ):
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = raw_tokens
            mock_collector_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_collector,
            )
            mock_collector_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.scheduler.jobs import daily_collection_job

            # Should not raise — narrative failure is caught
            await daily_collection_job(redis=None)

            # Main persist should still have been called
            mock_persist_results.assert_awaited_once()
