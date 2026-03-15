"""Tests for CycleDetector — market cycle phase classification.

TDD RED phase: write failing tests describing the desired behaviour.
"""

from __future__ import annotations

from app.analysis.cycle_detector import (
    CycleDetector,
    CycleIndicators,
    CyclePhase,
    CycleResult,
)

# ---------------------------------------------------------------------------
# CyclePhase enum
# ---------------------------------------------------------------------------


class TestCyclePhase:
    """CyclePhase must have exactly 4 members."""

    def test_accumulation_phase_exists(self) -> None:
        assert CyclePhase.ACCUMULATION.value == "accumulation"

    def test_bull_phase_exists(self) -> None:
        assert CyclePhase.BULL.value == "bull"

    def test_distribution_phase_exists(self) -> None:
        assert CyclePhase.DISTRIBUTION.value == "distribution"

    def test_bear_phase_exists(self) -> None:
        assert CyclePhase.BEAR.value == "bear"


# ---------------------------------------------------------------------------
# CycleIndicators dataclass
# ---------------------------------------------------------------------------


class TestCycleIndicators:
    """CycleIndicators carries raw market data for phase detection."""

    def test_create_indicators_with_all_fields(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.2,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.4e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=72,
            fear_greed_label="greed",
        )
        assert indicators.btc_dominance == 55.2
        assert indicators.btc_dominance_30d_ago == 52.0
        assert indicators.total_market_cap_usd == 2.4e12
        assert indicators.total_market_cap_200d_ma == 2.0e12
        assert indicators.fear_greed_index == 72
        assert indicators.fear_greed_label == "greed"

    def test_indicators_optional_200d_ma_defaults_none(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=55.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.total_market_cap_200d_ma is None

    def test_btc_dominance_rising(self) -> None:
        """When BTC dominance is higher than 30d ago, it's rising."""
        indicators = CycleIndicators(
            btc_dominance=58.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.btc_dominance_rising is True

    def test_btc_dominance_not_rising(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=48.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.btc_dominance_rising is False

    def test_market_cap_above_200d_ma(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=55.0,
            total_market_cap_usd=2.5e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.market_above_200d_ma is True

    def test_market_cap_below_200d_ma(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=55.0,
            total_market_cap_usd=1.5e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.market_above_200d_ma is False

    def test_market_above_200d_ma_none_when_missing(self) -> None:
        """If 200d MA is unavailable, the property returns None."""
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=55.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        assert indicators.market_above_200d_ma is None


# ---------------------------------------------------------------------------
# CycleResult dataclass
# ---------------------------------------------------------------------------


class TestCycleResult:
    """CycleResult must carry the detected phase, confidence, and indicators."""

    def test_create_result(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        result = CycleResult(
            phase=CyclePhase.ACCUMULATION,
            confidence=0.65,
            indicators=indicators,
        )
        assert result.phase == CyclePhase.ACCUMULATION
        assert result.confidence == 0.65
        assert result.indicators is indicators

    def test_result_to_dict(self) -> None:
        indicators = CycleIndicators(
            btc_dominance=55.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.0e12,
            fear_greed_index=72,
            fear_greed_label="greed",
        )
        result = CycleResult(
            phase=CyclePhase.BULL,
            confidence=0.80,
            indicators=indicators,
        )
        d = result.to_dict()
        assert d["phase"] == "bull"
        assert d["confidence"] == 0.80
        assert d["indicators"]["btc_dominance"] == 55.0
        assert d["indicators"]["fear_greed_index"] == 72


# ---------------------------------------------------------------------------
# CycleDetector.classify — deterministic phase classification
# ---------------------------------------------------------------------------


class TestCycleDetectorClassify:
    """CycleDetector.classify() should determine the market phase from indicators."""

    def test_bull_phase_high_greed_above_200d(self) -> None:
        """Extreme greed + market above 200d MA + falling BTC dom → BULL."""
        indicators = CycleIndicators(
            btc_dominance=45.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=3.0e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=80,
            fear_greed_label="extreme greed",
        )
        result = CycleDetector.classify(indicators)
        assert result.phase == CyclePhase.BULL
        assert result.confidence >= 0.6

    def test_bear_phase_extreme_fear_below_200d(self) -> None:
        """Extreme fear + market below 200d MA → BEAR."""
        indicators = CycleIndicators(
            btc_dominance=60.0,
            btc_dominance_30d_ago=55.0,
            total_market_cap_usd=1.0e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=15,
            fear_greed_label="extreme fear",
        )
        result = CycleDetector.classify(indicators)
        assert result.phase == CyclePhase.BEAR
        assert result.confidence >= 0.6

    def test_distribution_phase_greed_rising_btc_dom(self) -> None:
        """Greed but BTC dominance rising + market near 200d MA → DISTRIBUTION."""
        indicators = CycleIndicators(
            btc_dominance=58.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=2.1e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=65,
            fear_greed_label="greed",
        )
        result = CycleDetector.classify(indicators)
        assert result.phase == CyclePhase.DISTRIBUTION
        assert result.confidence >= 0.4

    def test_accumulation_phase_fear_near_200d(self) -> None:
        """Fear zone + market near/below 200d MA + BTC dom rising → ACCUMULATION."""
        indicators = CycleIndicators(
            btc_dominance=56.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=1.9e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=30,
            fear_greed_label="fear",
        )
        result = CycleDetector.classify(indicators)
        assert result.phase == CyclePhase.ACCUMULATION
        assert result.confidence >= 0.4

    def test_classify_without_200d_ma_still_works(self) -> None:
        """Graceful degradation when 200d MA is unavailable."""
        indicators = CycleIndicators(
            btc_dominance=45.0,
            btc_dominance_30d_ago=52.0,
            total_market_cap_usd=3.0e12,
            fear_greed_index=80,
            fear_greed_label="extreme greed",
        )
        result = CycleDetector.classify(indicators)
        # Should still produce a valid result, just with lower confidence
        assert isinstance(result.phase, CyclePhase)
        assert 0.0 <= result.confidence <= 1.0

    def test_neutral_market_defaults_accumulation(self) -> None:
        """Neutral/ambiguous signals → ACCUMULATION as default (conservative)."""
        indicators = CycleIndicators(
            btc_dominance=50.0,
            btc_dominance_30d_ago=50.0,
            total_market_cap_usd=2.0e12,
            total_market_cap_200d_ma=2.0e12,
            fear_greed_index=50,
            fear_greed_label="neutral",
        )
        result = CycleDetector.classify(indicators)
        assert result.phase == CyclePhase.ACCUMULATION
        assert result.confidence <= 0.5  # low confidence for ambiguous

    def test_confidence_always_between_0_and_1(self) -> None:
        """Confidence score must always be in [0, 1]."""
        for fg in [5, 25, 50, 75, 95]:
            indicators = CycleIndicators(
                btc_dominance=50.0,
                btc_dominance_30d_ago=50.0,
                total_market_cap_usd=2.0e12,
                total_market_cap_200d_ma=2.0e12,
                fear_greed_index=fg,
                fear_greed_label="test",
            )
            result = CycleDetector.classify(indicators)
            assert 0.0 <= result.confidence <= 1.0, f"confidence out of range for F&G={fg}"


# ---------------------------------------------------------------------------
# CycleDetector.cycle_score_adjustment — scoring weight for engine
# ---------------------------------------------------------------------------


class TestCycleScoreAdjustment:
    """The detector should provide a multiplier for the OpportunityEngine."""

    def test_bull_phase_returns_positive_boost(self) -> None:
        adj = CycleDetector.cycle_score_adjustment(CyclePhase.BULL)
        assert adj > 1.0  # boost

    def test_bear_phase_returns_negative_adjustment(self) -> None:
        adj = CycleDetector.cycle_score_adjustment(CyclePhase.BEAR)
        assert adj < 1.0  # dampen

    def test_accumulation_phase_neutral_to_slight_boost(self) -> None:
        adj = CycleDetector.cycle_score_adjustment(CyclePhase.ACCUMULATION)
        assert 0.9 <= adj <= 1.1

    def test_distribution_phase_slight_dampening(self) -> None:
        adj = CycleDetector.cycle_score_adjustment(CyclePhase.DISTRIBUTION)
        assert 0.8 <= adj <= 1.0
