"""Tests for backtesting.multi_cycle_collector — multi-cycle historical data.

TDD: RED phase — tests written first.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.backtesting.multi_cycle_collector import (
    CollectionProgress,
    CollectionResult,
    MultiCycleCollector,
)

# ---------------------------------------------------------------------------
# Helpers — build fake CoinGecko responses
# ---------------------------------------------------------------------------


def _make_cg_response(
    start_ts: float,
    n_days: int = 30,
    base_price: float = 100.0,
) -> dict[str, list[list[float]]]:
    """Build a minimal CoinGecko market_chart/range response."""
    day_ms = 86_400_000
    prices: list[list[float]] = []
    volumes: list[list[float]] = []
    caps: list[list[float]] = []
    for i in range(n_days):
        ts = start_ts + i * day_ms
        p = base_price + i
        prices.append([ts, p])
        volumes.append([ts, p * 1_000_000])
        caps.append([ts, p * 100_000_000])
    return {"prices": prices, "total_volumes": volumes, "market_caps": caps}


# ---------------------------------------------------------------------------
# CollectionProgress
# ---------------------------------------------------------------------------


class TestCollectionProgress:
    """CollectionProgress dataclass tests."""

    def test_progress_fields_are_set(self) -> None:
        p = CollectionProgress(
            cycle_name="cycle_1",
            total_tokens=15,
            completed_tokens=5,
            failed_tokens=1,
        )
        assert p.cycle_name == "cycle_1"
        assert p.total_tokens == 15
        assert p.completed_tokens == 5
        assert p.failed_tokens == 1

    def test_progress_pct(self) -> None:
        p = CollectionProgress(cycle_name="c", total_tokens=10, completed_tokens=5, failed_tokens=0)
        assert p.pct_complete == pytest.approx(50.0)

    def test_progress_pct_zero_total(self) -> None:
        p = CollectionProgress(cycle_name="c", total_tokens=0, completed_tokens=0, failed_tokens=0)
        assert p.pct_complete == 0.0


# ---------------------------------------------------------------------------
# CollectionResult
# ---------------------------------------------------------------------------


class TestCollectionResult:
    """CollectionResult dataclass tests."""

    def test_result_fields_are_set(self) -> None:
        r = CollectionResult(
            cycle_name="cycle_2",
            snapshots=[{"symbol": "BTC"}],
            errors={"ETH": "timeout"},
        )
        assert r.cycle_name == "cycle_2"
        assert len(r.snapshots) == 1
        assert "ETH" in r.errors

    def test_result_success_count(self) -> None:
        r = CollectionResult(
            cycle_name="c",
            snapshots=[{"symbol": "BTC"}, {"symbol": "ETH"}],
            errors={},
        )
        assert r.n_tokens_collected == 2

    def test_result_is_complete_with_no_errors(self) -> None:
        r = CollectionResult(cycle_name="c", snapshots=[], errors={})
        assert r.is_complete is True

    def test_result_is_not_complete_with_errors(self) -> None:
        r = CollectionResult(cycle_name="c", snapshots=[], errors={"X": "fail"})
        assert r.is_complete is False


# ---------------------------------------------------------------------------
# MultiCycleCollector
# ---------------------------------------------------------------------------


class TestMultiCycleCollector:
    """MultiCycleCollector class tests."""

    def test_init_defaults(self) -> None:
        collector = MultiCycleCollector()
        assert collector.delay_between_requests >= 0

    def test_init_custom_delay(self) -> None:
        collector = MultiCycleCollector(delay_between_requests=5.0)
        assert collector.delay_between_requests == 5.0

    @pytest.mark.asyncio
    async def test_collect_token_returns_snapshots(self) -> None:
        """Mocked CoinGecko fetch returns parsed snapshots for a token."""
        ts_base = 1577836800000.0  # 2020-01-01T00:00:00 UTC
        fake_resp = _make_cg_response(ts_base, n_days=5, base_price=100.0)

        collector = MultiCycleCollector(delay_between_requests=0)
        with patch.object(
            collector, "_fetch_market_chart", new_callable=AsyncMock, return_value=fake_resp
        ):
            snaps = await collector.collect_token(
                symbol="BTC",
                coingecko_id="bitcoin",
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
            )
        assert len(snaps) == 5
        assert snaps[0]["symbol"] == "BTC"
        assert "price_usd" in snaps[0]

    @pytest.mark.asyncio
    async def test_collect_token_empty_response_returns_empty(self) -> None:
        collector = MultiCycleCollector(delay_between_requests=0)
        with patch.object(
            collector,
            "_fetch_market_chart",
            new_callable=AsyncMock,
            return_value={"prices": [], "total_volumes": [], "market_caps": []},
        ):
            snaps = await collector.collect_token(
                symbol="BTC",
                coingecko_id="bitcoin",
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
            )
        assert snaps == []

    @pytest.mark.asyncio
    async def test_collect_token_api_error_raises(self) -> None:
        collector = MultiCycleCollector(delay_between_requests=0)
        with (
            patch.object(
                collector,
                "_fetch_market_chart",
                new_callable=AsyncMock,
                side_effect=RuntimeError("rate limited"),
            ),
            pytest.raises(RuntimeError, match="rate limited"),
        ):
            await collector.collect_token(
                symbol="BTC",
                coingecko_id="bitcoin",
                start_date=date(2020, 1, 1),
                end_date=date(2020, 1, 31),
            )

    @pytest.mark.asyncio
    async def test_collect_cycle_returns_result(self) -> None:
        """collect_cycle aggregates snapshots for all tokens in a cycle."""
        ts_base = 1577836800000.0
        fake_resp = _make_cg_response(ts_base, n_days=3, base_price=50.0)

        collector = MultiCycleCollector(delay_between_requests=0)
        with patch.object(
            collector, "_fetch_market_chart", new_callable=AsyncMock, return_value=fake_resp
        ):
            result = await collector.collect_cycle("cycle_1_2015_2018")

        assert isinstance(result, CollectionResult)
        assert result.cycle_name == "cycle_1_2015_2018"
        assert result.n_tokens_collected > 0
        assert len(result.snapshots) > 0

    @pytest.mark.asyncio
    async def test_collect_cycle_handles_partial_failures(self) -> None:
        """If some tokens fail, they appear in errors but others succeed."""
        call_count = 0

        async def _alternating_fetch(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise RuntimeError("simulated failure")
            ts_base = 1577836800000.0
            return _make_cg_response(ts_base, n_days=2, base_price=10.0)

        collector = MultiCycleCollector(delay_between_requests=0)
        with patch.object(
            collector, "_fetch_market_chart", new_callable=AsyncMock, side_effect=_alternating_fetch
        ):
            result = await collector.collect_cycle("cycle_1_2015_2018")

        assert len(result.errors) > 0
        assert result.n_tokens_collected > 0

    @pytest.mark.asyncio
    async def test_collect_cycle_unknown_cycle_raises(self) -> None:
        collector = MultiCycleCollector(delay_between_requests=0)
        with pytest.raises(KeyError):
            await collector.collect_cycle("nonexistent_cycle")

    @pytest.mark.asyncio
    async def test_build_monthly_snapshots_integration(self) -> None:
        """Collected daily snapshots can be reduced to monthly."""
        # 60 days of data → should produce 2 months
        ts_base = 1577836800000.0  # 2020-01-01
        fake_resp = _make_cg_response(ts_base, n_days=60, base_price=100.0)

        collector = MultiCycleCollector(delay_between_requests=0)
        with patch.object(
            collector, "_fetch_market_chart", new_callable=AsyncMock, return_value=fake_resp
        ):
            snaps = await collector.collect_token(
                symbol="BTC",
                coingecko_id="bitcoin",
                start_date=date(2020, 1, 1),
                end_date=date(2020, 3, 1),
            )
        monthly = collector.to_monthly(snaps)
        assert len(monthly) >= 2
        # Each monthly snapshot should have exactly one per month
        months = {(s["snapshot_date"].year, s["snapshot_date"].month) for s in monthly}
        assert len(months) == len(monthly)
