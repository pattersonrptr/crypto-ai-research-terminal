"""Tests for app.backtesting.historical_data_collector — TDD Red→Green.

The historical data collector fetches token data from CoinGecko
``/coins/{id}/market_chart/range`` and converts it into snapshot dicts
suitable for storage in the ``historical_snapshots`` table.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.backtesting.historical_data_collector import (
    VALIDATION_TOKENS,
    build_monthly_snapshots,
    parse_market_chart_to_snapshots,
)

# ---------------------------------------------------------------------------
# TestParseMarketChartToSnapshots
# ---------------------------------------------------------------------------


class TestParseMarketChartToSnapshots:
    """Tests for parse_market_chart_to_snapshots()."""

    @staticmethod
    def _make_payload(n_days: int = 30) -> dict[str, Any]:
        """Build a fake CoinGecko market_chart/range response with n_days."""
        base_ts_ms = datetime(2020, 1, 1, tzinfo=UTC).timestamp() * 1000
        day_ms = 86_400_000

        prices = [[base_ts_ms + i * day_ms, 100.0 + i] for i in range(n_days)]
        volumes = [[base_ts_ms + i * day_ms, 1_000_000.0 + i * 100] for i in range(n_days)]
        mcaps = [[base_ts_ms + i * day_ms, 10_000_000.0 + i * 1000] for i in range(n_days)]

        return {"prices": prices, "total_volumes": volumes, "market_caps": mcaps}

    def test_parse_returns_list_of_dicts(self) -> None:
        """parse_market_chart_to_snapshots must return list of snapshot dicts."""
        payload = self._make_payload()
        result = parse_market_chart_to_snapshots("BTC", payload)
        assert isinstance(result, list)
        assert len(result) == 30
        assert isinstance(result[0], dict)

    def test_parse_snapshot_has_required_keys(self) -> None:
        """Each snapshot dict must have symbol, snapshot_date, price_usd, etc."""
        payload = self._make_payload(n_days=5)
        result = parse_market_chart_to_snapshots("ETH", payload)
        snap = result[0]
        assert snap["symbol"] == "ETH"
        assert isinstance(snap["snapshot_date"], date)
        assert snap["price_usd"] > 0
        assert snap["volume_usd"] > 0
        assert snap["market_cap_usd"] > 0

    def test_parse_empty_payload_returns_empty_list(self) -> None:
        """Empty or missing prices must return []."""
        assert parse_market_chart_to_snapshots("BTC", {}) == []
        assert parse_market_chart_to_snapshots("BTC", {"prices": []}) == []

    def test_parse_deduplicates_by_date(self) -> None:
        """If multiple data points fall on the same day, keep only the last."""
        base_ts_ms = datetime(2020, 1, 1, tzinfo=UTC).timestamp() * 1000
        # Two points on the same day (12h apart)
        payload: dict[str, Any] = {
            "prices": [
                [base_ts_ms, 100.0],
                [base_ts_ms + 43_200_000, 105.0],  # 12h later, same day
            ],
            "total_volumes": [
                [base_ts_ms, 1_000_000.0],
                [base_ts_ms + 43_200_000, 1_100_000.0],
            ],
            "market_caps": [
                [base_ts_ms, 10_000_000.0],
                [base_ts_ms + 43_200_000, 10_500_000.0],
            ],
        }
        result = parse_market_chart_to_snapshots("SOL", payload)
        assert len(result) == 1
        # Should keep the last value for that day
        assert result[0]["price_usd"] == pytest.approx(105.0)

    def test_parse_sorts_by_date(self) -> None:
        """Snapshots must be sorted by snapshot_date ascending."""
        payload = self._make_payload(n_days=10)
        result = parse_market_chart_to_snapshots("BTC", payload)
        dates = [s["snapshot_date"] for s in result]
        assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# TestBuildMonthlySnapshots
# ---------------------------------------------------------------------------


class TestBuildMonthlySnapshots:
    """Tests for build_monthly_snapshots()."""

    def test_build_monthly_picks_first_of_month(self) -> None:
        """build_monthly_snapshots must pick the snapshot closest to 1st of each month."""
        daily_snapshots = [
            {
                "symbol": "BTC",
                "snapshot_date": date(2020, 1, d),
                "price_usd": 100.0 + d,
                "market_cap_usd": 1_000_000.0,
                "volume_usd": 100_000.0,
            }
            for d in range(1, 32)
        ] + [
            {
                "symbol": "BTC",
                "snapshot_date": date(2020, 2, d),
                "price_usd": 200.0 + d,
                "market_cap_usd": 2_000_000.0,
                "volume_usd": 200_000.0,
            }
            for d in range(1, 29)
        ]
        monthly = build_monthly_snapshots(daily_snapshots)
        assert len(monthly) == 2
        assert monthly[0]["snapshot_date"] == date(2020, 1, 1)
        assert monthly[1]["snapshot_date"] == date(2020, 2, 1)

    def test_build_monthly_empty_input_returns_empty(self) -> None:
        """build_monthly_snapshots with empty input returns []."""
        assert build_monthly_snapshots([]) == []

    def test_build_monthly_preserves_all_fields(self) -> None:
        """Monthly snapshots must preserve all fields from the daily snapshot."""
        daily = [
            {
                "symbol": "ETH",
                "snapshot_date": date(2020, 3, 1),
                "price_usd": 200.0,
                "market_cap_usd": 20_000_000_000.0,
                "volume_usd": 5_000_000_000.0,
                "categories": "Layer 1",
            }
        ]
        monthly = build_monthly_snapshots(daily)
        assert monthly[0]["symbol"] == "ETH"
        assert monthly[0]["categories"] == "Layer 1"


# ---------------------------------------------------------------------------
# TestValidationTokens
# ---------------------------------------------------------------------------


class TestValidationTokens:
    """Tests for the VALIDATION_TOKENS constant."""

    def test_validation_tokens_contains_at_least_10_entries(self) -> None:
        """VALIDATION_TOKENS must have >= 10 token entries."""
        assert len(VALIDATION_TOKENS) >= 10

    def test_validation_tokens_keys_are_tickers(self) -> None:
        """Keys must be uppercase ticker symbols."""
        for key in VALIDATION_TOKENS:
            assert key == key.upper()
            assert len(key) <= 10

    def test_validation_tokens_values_are_coingecko_ids(self) -> None:
        """Values must be non-empty CoinGecko coin IDs."""
        for _ticker, cg_id in VALIDATION_TOKENS.items():
            assert isinstance(cg_id, str)
            assert len(cg_id) > 0
