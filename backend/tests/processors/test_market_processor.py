"""Tests for MarketProcessor.

Validates volume/mcap ratio, velocity (price change %), and ATH distance computation.
"""

import pytest

from app.processors.market_processor import MarketProcessor


class TestMarketProcessorVolumeMcapRatio:
    """volume_mcap_ratio = volume_24h / market_cap."""

    def test_market_processor_volume_mcap_ratio_returns_correct_value(self) -> None:
        result = MarketProcessor.volume_mcap_ratio(
            volume_24h_usd=1_000_000.0, market_cap_usd=10_000_000.0
        )
        assert result == pytest.approx(0.1)

    def test_market_processor_volume_mcap_ratio_zero_market_cap_returns_zero(self) -> None:
        result = MarketProcessor.volume_mcap_ratio(volume_24h_usd=500.0, market_cap_usd=0.0)
        assert result == 0.0

    def test_market_processor_volume_mcap_ratio_zero_volume_returns_zero(self) -> None:
        result = MarketProcessor.volume_mcap_ratio(volume_24h_usd=0.0, market_cap_usd=1_000_000.0)
        assert result == 0.0


class TestMarketProcessorPriceVelocity:
    """price_velocity = (current - previous) / previous * 100  (percentage change)."""

    def test_market_processor_price_velocity_positive_change(self) -> None:
        result = MarketProcessor.price_velocity(current_price=110.0, previous_price=100.0)
        assert result == pytest.approx(10.0)

    def test_market_processor_price_velocity_negative_change(self) -> None:
        result = MarketProcessor.price_velocity(current_price=90.0, previous_price=100.0)
        assert result == pytest.approx(-10.0)

    def test_market_processor_price_velocity_zero_previous_returns_zero(self) -> None:
        result = MarketProcessor.price_velocity(current_price=100.0, previous_price=0.0)
        assert result == 0.0

    def test_market_processor_price_velocity_unchanged_price_returns_zero(self) -> None:
        result = MarketProcessor.price_velocity(current_price=50.0, previous_price=50.0)
        assert result == pytest.approx(0.0)


class TestMarketProcessorAthDistance:
    """ath_distance = (ath - current) / ath * 100  (percentage below ATH)."""

    def test_market_processor_ath_distance_returns_correct_value(self) -> None:
        result = MarketProcessor.ath_distance(current_price=50.0, ath_price=100.0)
        assert result == pytest.approx(50.0)

    def test_market_processor_ath_distance_at_ath_returns_zero(self) -> None:
        result = MarketProcessor.ath_distance(current_price=100.0, ath_price=100.0)
        assert result == pytest.approx(0.0)

    def test_market_processor_ath_distance_zero_ath_returns_zero(self) -> None:
        result = MarketProcessor.ath_distance(current_price=50.0, ath_price=0.0)
        assert result == 0.0


class TestMarketProcessorProcess:
    """process() applies all metrics to a raw market-data dict."""

    def test_market_processor_process_returns_dict_with_derived_fields(self) -> None:
        raw = {
            "price_usd": 110.0,
            "market_cap_usd": 10_000_000.0,
            "volume_24h_usd": 1_000_000.0,
            "ath_usd": 200.0,
        }
        result = MarketProcessor.process(raw, previous_price=100.0)
        assert "volume_mcap_ratio" in result
        assert "price_velocity" in result
        assert "ath_distance_pct" in result

    def test_market_processor_process_preserves_input_fields(self) -> None:
        raw = {
            "price_usd": 100.0,
            "market_cap_usd": 1_000_000.0,
            "volume_24h_usd": 100_000.0,
            "ath_usd": 200.0,
        }
        result = MarketProcessor.process(raw, previous_price=90.0)
        assert result["price_usd"] == 100.0
        assert result["market_cap_usd"] == 1_000_000.0
