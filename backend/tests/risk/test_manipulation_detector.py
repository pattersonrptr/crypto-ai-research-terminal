"""Tests for ManipulationDetector.

Detects market manipulation signals:
- Pump & dump patterns (rapid price spike followed by crash)
- Wash trading (self-dealing to inflate volume)
- Coordinated social activity (bot-like posts, timing correlation)
"""

import pytest

from app.risk.manipulation_detector import (
    ManipulationDetector,
    ManipulationRiskResult,
)


class TestManipulationDetectorAnalyze:
    """ManipulationDetector.analyze() returns a ManipulationRiskResult."""

    def test_manipulation_detector_analyze_returns_result_dataclass(self) -> None:
        data = {
            "price_history": [100.0, 101.0, 102.0, 101.5, 102.5],
            "volume_history": [1000.0, 1100.0, 1050.0, 1200.0, 1150.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert isinstance(result, ManipulationRiskResult)

    def test_manipulation_detector_analyze_normal_market_scores_low(self) -> None:
        """Normal market activity should have low manipulation risk."""
        data = {
            "price_history": [100.0, 101.0, 102.0, 101.5, 102.5, 103.0],
            "volume_history": [1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1100.0],
            "social_post_times": [1.0, 100.0, 250.0, 500.0, 800.0],  # spread out
            "unique_traders_ratio": 0.75,
        }
        result = ManipulationDetector.analyze(data)
        assert 0.0 <= result.risk_score <= 0.3

    def test_manipulation_detector_analyze_suspicious_activity_scores_high(self) -> None:
        """Pump-and-dump + wash trading + coordinated social = high risk."""
        data = {
            # Pump and dump pattern: rapid spike then crash
            "price_history": [100.0, 150.0, 200.0, 180.0, 120.0, 80.0],
            # Suspiciously high volume during pump
            "volume_history": [1000.0, 5000.0, 8000.0, 3000.0, 2000.0, 1500.0],
            # Coordinated social posts (very close timestamps)
            "social_post_times": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
            # Low unique traders = wash trading
            "unique_traders_ratio": 0.15,
        }
        result = ManipulationDetector.analyze(data)
        assert result.risk_score >= 0.7


class TestManipulationDetectorPumpDump:
    """Tests for pump & dump pattern detection."""

    def test_manipulation_detector_detects_pump_dump_pattern(self) -> None:
        """Price spike > 50% followed by drop > 30% = pump & dump."""
        data = {
            "price_history": [100.0, 160.0, 200.0, 180.0, 130.0, 100.0],
            "volume_history": [1000.0] * 6,
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert result.pump_dump_detected is True

    def test_manipulation_detector_no_pump_dump_in_stable_market(self) -> None:
        """Stable price movement should not trigger pump & dump flag."""
        data = {
            "price_history": [100.0, 102.0, 104.0, 103.0, 105.0, 106.0],
            "volume_history": [1000.0] * 6,
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert result.pump_dump_detected is False


class TestManipulationDetectorWashTrading:
    """Tests for wash trading detection."""

    def test_manipulation_detector_detects_wash_trading(self) -> None:
        """Low unique traders ratio (< 30%) indicates wash trading."""
        data = {
            "price_history": [100.0, 101.0, 102.0],
            "volume_history": [1000.0, 1100.0, 1050.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.20,  # Only 20% unique traders
        }
        result = ManipulationDetector.analyze(data)
        assert result.wash_trading_detected is True

    def test_manipulation_detector_no_wash_trading_high_unique_ratio(self) -> None:
        """High unique traders ratio should not flag wash trading."""
        data = {
            "price_history": [100.0, 101.0, 102.0],
            "volume_history": [1000.0, 1100.0, 1050.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.70,  # 70% unique traders
        }
        result = ManipulationDetector.analyze(data)
        assert result.wash_trading_detected is False


class TestManipulationDetectorCoordinatedSocial:
    """Tests for coordinated social activity detection."""

    def test_manipulation_detector_detects_coordinated_social(self) -> None:
        """Many posts in short time window indicates coordination."""
        data = {
            "price_history": [100.0, 101.0, 102.0],
            "volume_history": [1000.0, 1100.0, 1050.0],
            # 10 posts within 1 minute
            "social_post_times": [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert result.coordinated_social_detected is True

    def test_manipulation_detector_no_coordination_spread_posts(self) -> None:
        """Spread out posts should not trigger coordination flag."""
        data = {
            "price_history": [100.0, 101.0, 102.0],
            "volume_history": [1000.0, 1100.0, 1050.0],
            # Posts spread over hours (in seconds)
            "social_post_times": [0.0, 3600.0, 7200.0, 10800.0],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert result.coordinated_social_detected is False

    def test_manipulation_detector_no_coordination_empty_posts(self) -> None:
        """No social posts should not trigger coordination flag."""
        data = {
            "price_history": [100.0, 101.0, 102.0],
            "volume_history": [1000.0, 1100.0, 1050.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert result.coordinated_social_detected is False


class TestManipulationDetectorValidation:
    """ManipulationDetector validates input data."""

    def test_manipulation_detector_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            ManipulationDetector.analyze({})

    def test_manipulation_detector_raises_on_empty_price_history(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "price_history": [],
            "volume_history": [1000.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        with pytest.raises(ScoringError):
            ManipulationDetector.analyze(data)

    def test_manipulation_detector_raises_on_invalid_unique_ratio(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "price_history": [100.0, 101.0],
            "volume_history": [1000.0, 1100.0],
            "social_post_times": [],
            "unique_traders_ratio": 1.5,  # > 1.0 invalid
        }
        with pytest.raises(ScoringError):
            ManipulationDetector.analyze(data)

    def test_manipulation_detector_handles_short_price_history(self) -> None:
        """Should work with minimal data (at least 2 data points)."""
        data = {
            "price_history": [100.0, 101.0],
            "volume_history": [1000.0, 1100.0],
            "social_post_times": [],
            "unique_traders_ratio": 0.8,
        }
        result = ManipulationDetector.analyze(data)
        assert isinstance(result, ManipulationRiskResult)
