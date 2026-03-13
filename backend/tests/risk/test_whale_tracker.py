"""Tests for WhaleTracker.

Tracks whale activity:
- Top 50 wallet holdings and concentration
- Accumulation/distribution patterns
- Large transaction detection
"""

import pytest

from app.risk.whale_tracker import WhaleAnalysisResult, WhaleTracker


class TestWhaleTrackerAnalyze:
    """WhaleTracker.analyze() returns a WhaleAnalysisResult."""

    def test_whale_tracker_analyze_returns_result_dataclass(self) -> None:
        data = {
            "wallet_balances": [1000.0, 500.0, 200.0, 100.0, 50.0],
            "total_supply": 10000.0,
            "balance_changes_24h": [10.0, -5.0, 2.0, 0.0, -1.0],
        }
        result = WhaleTracker.analyze(data)
        assert isinstance(result, WhaleAnalysisResult)

    def test_whale_tracker_analyze_low_concentration_scores_low(self) -> None:
        """Decentralized holdings should have low whale risk."""
        data = {
            # Well distributed across many wallets - top 10 hold only 10%
            "wallet_balances": [10.0] * 100,  # 100 wallets, 1% each
            "total_supply": 1000.0,
            "balance_changes_24h": [0.0] * 100,
        }
        result = WhaleTracker.analyze(data)
        # Top 10 hold 10% of supply → risk = 10%/50% = 0.2
        assert 0.0 <= result.concentration_risk <= 0.3

    def test_whale_tracker_analyze_high_concentration_scores_high(self) -> None:
        """Concentrated holdings should have high whale risk."""
        data = {
            # Top wallet holds 60%, others much smaller
            "wallet_balances": [6000.0, 1000.0, 500.0, 300.0, 200.0],
            "total_supply": 10000.0,
            "balance_changes_24h": [0.0] * 5,
        }
        result = WhaleTracker.analyze(data)
        assert result.concentration_risk >= 0.7


class TestWhaleTrackerConcentration:
    """Tests for wallet concentration metrics."""

    def test_whale_tracker_calculates_top10_concentration(self) -> None:
        data = {
            "wallet_balances": [
                1000.0,
                900.0,
                800.0,
                700.0,
                600.0,
                500.0,
                400.0,
                300.0,
                200.0,
                100.0,
                50.0,
                40.0,
                30.0,
                20.0,
                10.0,
            ],
            "total_supply": 5650.0,  # sum of all
            "balance_changes_24h": [0.0] * 15,
        }
        result = WhaleTracker.analyze(data)
        # Top 10 hold 5500 out of 5650 = 97.3%
        expected = 5500.0 / 5650.0
        assert abs(result.top10_concentration - expected) < 0.01

    def test_whale_tracker_calculates_top50_concentration(self) -> None:
        data = {
            "wallet_balances": [100.0] * 60,  # 60 wallets
            "total_supply": 6000.0,
            "balance_changes_24h": [0.0] * 60,
        }
        result = WhaleTracker.analyze(data)
        # Top 50 hold 5000 out of 6000 = 83.3%
        expected = 5000.0 / 6000.0
        assert abs(result.top50_concentration - expected) < 0.01

    def test_whale_tracker_handles_fewer_than_50_wallets(self) -> None:
        data = {
            "wallet_balances": [500.0, 300.0, 200.0],  # Only 3 wallets
            "total_supply": 1000.0,
            "balance_changes_24h": [0.0] * 3,
        }
        result = WhaleTracker.analyze(data)
        # All wallets = 100% for both top10 and top50
        assert result.top50_concentration == 1.0


class TestWhaleTrackerAccumulationDistribution:
    """Tests for accumulation/distribution detection."""

    def test_whale_tracker_detects_accumulation(self) -> None:
        """Net positive balance changes = accumulation."""
        data = {
            "wallet_balances": [1000.0, 500.0, 200.0],
            "total_supply": 2000.0,
            # Whales buying: +100, +50, +20
            "balance_changes_24h": [100.0, 50.0, 20.0],
        }
        result = WhaleTracker.analyze(data)
        assert result.accumulation_signal > 0
        assert result.distribution_signal == 0

    def test_whale_tracker_detects_distribution(self) -> None:
        """Net negative balance changes = distribution."""
        data = {
            "wallet_balances": [1000.0, 500.0, 200.0],
            "total_supply": 2000.0,
            # Whales selling: -100, -50, -20
            "balance_changes_24h": [-100.0, -50.0, -20.0],
        }
        result = WhaleTracker.analyze(data)
        assert result.distribution_signal > 0
        assert result.accumulation_signal == 0

    def test_whale_tracker_neutral_no_signals(self) -> None:
        """Balanced changes = neutral."""
        data = {
            "wallet_balances": [1000.0, 500.0, 200.0],
            "total_supply": 2000.0,
            # Balanced: +50, -50, 0
            "balance_changes_24h": [50.0, -50.0, 0.0],
        }
        result = WhaleTracker.analyze(data)
        # Net change is ~0, both signals should be low
        assert abs(result.accumulation_signal - result.distribution_signal) < 0.1


class TestWhaleTrackerLargeTransactions:
    """Tests for large transaction detection."""

    def test_whale_tracker_flags_large_movements(self) -> None:
        """Large balance changes relative to supply should be flagged."""
        data = {
            "wallet_balances": [5000.0, 500.0, 200.0],
            "total_supply": 10000.0,
            # Top wallet moved 10% of supply
            "balance_changes_24h": [1000.0, 0.0, 0.0],
        }
        result = WhaleTracker.analyze(data)
        assert result.large_movements_detected is True

    def test_whale_tracker_no_flag_small_movements(self) -> None:
        """Small balance changes should not be flagged."""
        data = {
            "wallet_balances": [1000.0, 500.0, 200.0],
            "total_supply": 10000.0,
            # Small movements < 1% of supply
            "balance_changes_24h": [10.0, -5.0, 2.0],
        }
        result = WhaleTracker.analyze(data)
        assert result.large_movements_detected is False


class TestWhaleTrackerValidation:
    """WhaleTracker validates input data."""

    def test_whale_tracker_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            WhaleTracker.analyze({})

    def test_whale_tracker_raises_on_empty_wallets(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "wallet_balances": [],
            "total_supply": 1000.0,
            "balance_changes_24h": [],
        }
        with pytest.raises(ScoringError):
            WhaleTracker.analyze(data)

    def test_whale_tracker_raises_on_zero_supply(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "wallet_balances": [100.0, 50.0],
            "total_supply": 0.0,
            "balance_changes_24h": [0.0, 0.0],
        }
        with pytest.raises(ScoringError):
            WhaleTracker.analyze(data)

    def test_whale_tracker_raises_on_mismatched_lengths(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "wallet_balances": [100.0, 50.0, 25.0],
            "total_supply": 175.0,
            "balance_changes_24h": [0.0, 0.0],  # Wrong length
        }
        with pytest.raises(ScoringError):
            WhaleTracker.analyze(data)
