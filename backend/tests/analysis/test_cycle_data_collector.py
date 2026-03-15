"""Tests for CycleDataCollector — fetching market cycle indicators.

TDD RED phase: tests for Fear & Greed API + CoinGecko global data.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.analysis.cycle_data_collector import CycleDataCollector
from app.analysis.cycle_detector import CycleIndicators

# ---------------------------------------------------------------------------
# Fear & Greed index fetching
# ---------------------------------------------------------------------------


class TestFetchFearGreedIndex:
    """CycleDataCollector should fetch the current Fear & Greed value."""

    @pytest.mark.asyncio
    async def test_fetch_fear_greed_returns_index_and_label(self) -> None:
        """Happy path: Alternative.me returns valid JSON."""
        mock_response = {
            "data": [
                {
                    "value": "72",
                    "value_classification": "Greed",
                    "timestamp": "1700000000",
                }
            ]
        }
        collector = CycleDataCollector()
        with patch.object(
            collector,
            "_http_get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            index, label = await collector.fetch_fear_greed()

        assert index == 72
        assert label == "Greed"

    @pytest.mark.asyncio
    async def test_fetch_fear_greed_fallback_on_error(self) -> None:
        """On API error, return neutral defaults (50, 'unavailable')."""
        collector = CycleDataCollector()
        with patch.object(
            collector,
            "_http_get",
            new_callable=AsyncMock,
            side_effect=Exception("timeout"),
        ):
            index, label = await collector.fetch_fear_greed()

        assert index == 50
        assert label == "unavailable"


# ---------------------------------------------------------------------------
# BTC dominance fetching
# ---------------------------------------------------------------------------


class TestFetchBtcDominance:
    """CycleDataCollector should fetch BTC dominance from CoinGecko global."""

    @pytest.mark.asyncio
    async def test_fetch_btc_dominance_returns_current(self) -> None:
        mock_response = {
            "data": {
                "market_cap_percentage": {"btc": 55.2, "eth": 16.3},
                "total_market_cap": {"usd": 2.4e12},
            }
        }
        collector = CycleDataCollector()
        with patch.object(
            collector,
            "_http_get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            dominance, total_mcap = await collector.fetch_btc_dominance()

        assert dominance == pytest.approx(55.2)
        assert total_mcap == pytest.approx(2.4e12)

    @pytest.mark.asyncio
    async def test_fetch_btc_dominance_fallback_on_error(self) -> None:
        """On API error, return safe defaults."""
        collector = CycleDataCollector()
        with patch.object(
            collector,
            "_http_get",
            new_callable=AsyncMock,
            side_effect=Exception("rate limit"),
        ):
            dominance, total_mcap = await collector.fetch_btc_dominance()

        assert dominance == 50.0
        assert total_mcap == 0.0


# ---------------------------------------------------------------------------
# Full indicator assembly
# ---------------------------------------------------------------------------


class TestCollectIndicators:
    """CycleDataCollector.collect_indicators() should assemble CycleIndicators."""

    @pytest.mark.asyncio
    async def test_collect_indicators_assembles_all_fields(self) -> None:
        collector = CycleDataCollector()

        with (
            patch.object(
                collector,
                "fetch_fear_greed",
                new_callable=AsyncMock,
                return_value=(72, "Greed"),
            ),
            patch.object(
                collector,
                "fetch_btc_dominance",
                new_callable=AsyncMock,
                return_value=(55.2, 2.4e12),
            ),
        ):
            indicators = await collector.collect_indicators(btc_dominance_30d_ago=52.0)

        assert isinstance(indicators, CycleIndicators)
        assert indicators.btc_dominance == 55.2
        assert indicators.btc_dominance_30d_ago == 52.0
        assert indicators.total_market_cap_usd == pytest.approx(2.4e12)
        assert indicators.fear_greed_index == 72
        assert indicators.fear_greed_label == "Greed"

    @pytest.mark.asyncio
    async def test_collect_indicators_with_200d_ma(self) -> None:
        collector = CycleDataCollector()

        with (
            patch.object(
                collector,
                "fetch_fear_greed",
                new_callable=AsyncMock,
                return_value=(50, "Neutral"),
            ),
            patch.object(
                collector,
                "fetch_btc_dominance",
                new_callable=AsyncMock,
                return_value=(50.0, 2.0e12),
            ),
        ):
            indicators = await collector.collect_indicators(
                btc_dominance_30d_ago=50.0,
                total_market_cap_200d_ma=1.8e12,
            )

        assert indicators.total_market_cap_200d_ma == pytest.approx(1.8e12)

    @pytest.mark.asyncio
    async def test_collect_indicators_graceful_on_all_failures(self) -> None:
        """Even if all APIs fail, we get a valid CycleIndicators with defaults."""
        collector = CycleDataCollector()

        with (
            patch.object(
                collector,
                "fetch_fear_greed",
                new_callable=AsyncMock,
                return_value=(50, "unavailable"),
            ),
            patch.object(
                collector,
                "fetch_btc_dominance",
                new_callable=AsyncMock,
                return_value=(50.0, 0.0),
            ),
        ):
            indicators = await collector.collect_indicators(btc_dominance_30d_ago=50.0)

        assert isinstance(indicators, CycleIndicators)
        assert indicators.fear_greed_index == 50
        assert indicators.btc_dominance == 50.0
