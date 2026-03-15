"""Tests for alert generation integration in the daily collection pipeline.

Verifies that daily_collection_job runs AlertEvaluator after scoring and
persists any triggered alerts.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.alert import Alert


def _make_raw_token(
    symbol: str,
    *,
    categories: list[str] | None = None,
) -> dict[str, Any]:
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


class TestPipelineAlertIntegration:
    """daily_collection_job runs AlertEvaluator and persists triggered alerts."""

    @pytest.mark.asyncio
    async def test_daily_job_calls_alert_evaluator(self) -> None:
        """Pipeline should evaluate alerts after scoring."""
        raw_tokens = [_make_raw_token("AAA"), _make_raw_token("BBB")]

        fake_alert = MagicMock(spec=Alert)

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_coll_cls,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.build_narrative_snapshot_from_categories",
                return_value=[],
            ),
            patch(
                "app.scheduler.jobs.persist_narrative_snapshot",
                new_callable=AsyncMock,
            ),
            patch(
                "app.scheduler.jobs.evaluate_and_persist_alerts",
                new_callable=AsyncMock,
                return_value=[fake_alert],
            ) as mock_eval,
        ):
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = raw_tokens
            mock_coll_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_collector,
            )
            mock_coll_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.scheduler.jobs import daily_collection_job

            await daily_collection_job(redis=None)

            mock_eval.assert_called_once()
            # First arg must be the scored results list
            call_args = mock_eval.call_args[0][0]
            assert isinstance(call_args, list)

    @pytest.mark.asyncio
    async def test_daily_job_alert_failure_does_not_break_pipeline(self) -> None:
        """Alert evaluation failure must not crash the pipeline."""
        raw_tokens = [_make_raw_token("ZZZ")]

        with (
            patch("app.scheduler.jobs.CoinGeckoCollector") as mock_coll_cls,
            patch("app.scheduler.jobs._persist_results", new_callable=AsyncMock),
            patch(
                "app.scheduler.jobs.build_narrative_snapshot_from_categories",
                return_value=[],
            ),
            patch(
                "app.scheduler.jobs.persist_narrative_snapshot",
                new_callable=AsyncMock,
            ),
            patch(
                "app.scheduler.jobs.evaluate_and_persist_alerts",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
        ):
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = raw_tokens
            mock_coll_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_collector,
            )
            mock_coll_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.scheduler.jobs import daily_collection_job

            # Should not raise
            await daily_collection_job(redis=None)
