"""Tests for TokenomicsRisk.

Evaluates tokenomics-related risk:
- Unlock calendar (>5% unlock in 30 days = alert)
- Inflation rate
- Vesting schedule analysis
"""

import pytest

from app.risk.tokenomics_risk import TokenomicsRisk, TokenomicsRiskResult


class TestTokenomicsRiskAnalyze:
    """TokenomicsRisk.analyze() returns a TokenomicsRiskResult."""

    def test_tokenomics_risk_analyze_returns_result_dataclass(self) -> None:
        data = {
            "circulating_supply": 1_000_000.0,
            "total_supply": 2_000_000.0,
            "unlock_schedule": [],  # No scheduled unlocks
            "annual_inflation_rate": 0.02,  # 2%
        }
        result = TokenomicsRisk.analyze(data)
        assert isinstance(result, TokenomicsRiskResult)

    def test_tokenomics_risk_analyze_healthy_tokenomics_scores_low(self) -> None:
        """No upcoming unlocks and low inflation = low risk."""
        data = {
            "circulating_supply": 900_000.0,
            "total_supply": 1_000_000.0,  # 90% already circulating
            "unlock_schedule": [],
            "annual_inflation_rate": 0.01,  # 1%
        }
        result = TokenomicsRisk.analyze(data)
        assert 0.0 <= result.risk_score <= 0.3

    def test_tokenomics_risk_analyze_risky_tokenomics_scores_high(self) -> None:
        """Large upcoming unlock + high inflation = high risk."""
        data = {
            "circulating_supply": 200_000.0,
            "total_supply": 1_000_000.0,  # Only 20% circulating
            # 10% unlock in 15 days
            "unlock_schedule": [{"days_until": 15, "amount_pct": 0.10}],
            "annual_inflation_rate": 0.15,  # 15%
        }
        result = TokenomicsRisk.analyze(data)
        assert result.risk_score >= 0.7


class TestTokenomicsRiskUnlockCalendar:
    """Tests for unlock schedule analysis."""

    def test_tokenomics_risk_flags_large_unlock_in_30_days(self) -> None:
        """>5% unlock in 30 days triggers alert."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [{"days_until": 20, "amount_pct": 0.08}],  # 8% in 20 days
            "annual_inflation_rate": 0.02,
        }
        result = TokenomicsRisk.analyze(data)
        assert result.unlock_alert is True
        assert result.unlock_30d_pct >= 0.05

    def test_tokenomics_risk_no_alert_small_unlock(self) -> None:
        """<5% unlock in 30 days = no alert."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [{"days_until": 20, "amount_pct": 0.03}],  # 3% in 20 days
            "annual_inflation_rate": 0.02,
        }
        result = TokenomicsRisk.analyze(data)
        assert result.unlock_alert is False

    def test_tokenomics_risk_no_alert_unlock_beyond_30_days(self) -> None:
        """Unlock beyond 30 days doesn't trigger 30-day alert."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [{"days_until": 45, "amount_pct": 0.10}],  # 10% in 45 days
            "annual_inflation_rate": 0.02,
        }
        result = TokenomicsRisk.analyze(data)
        assert result.unlock_alert is False
        assert result.unlock_30d_pct == 0.0

    def test_tokenomics_risk_aggregates_multiple_unlocks(self) -> None:
        """Multiple unlocks in 30 days should aggregate."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [
                {"days_until": 10, "amount_pct": 0.03},  # 3%
                {"days_until": 25, "amount_pct": 0.04},  # 4%
            ],  # Total 7% in 30 days
            "annual_inflation_rate": 0.02,
        }
        result = TokenomicsRisk.analyze(data)
        assert result.unlock_alert is True
        assert abs(result.unlock_30d_pct - 0.07) < 0.001


class TestTokenomicsRiskInflation:
    """Tests for inflation rate analysis."""

    def test_tokenomics_risk_high_inflation_increases_risk(self) -> None:
        base = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,  # 2%
        }
        high_inflation = {**base, "annual_inflation_rate": 0.20}  # 20%

        base_result = TokenomicsRisk.analyze(base)
        high_result = TokenomicsRisk.analyze(high_inflation)
        assert high_result.risk_score > base_result.risk_score

    def test_tokenomics_risk_flags_high_inflation(self) -> None:
        """>10% annual inflation is flagged."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.15,  # 15%
        }
        result = TokenomicsRisk.analyze(data)
        assert result.high_inflation is True

    def test_tokenomics_risk_no_flag_normal_inflation(self) -> None:
        """<10% annual inflation is not flagged."""
        data = {
            "circulating_supply": 500_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.05,  # 5%
        }
        result = TokenomicsRisk.analyze(data)
        assert result.high_inflation is False


class TestTokenomicsRiskSupplyMetrics:
    """Tests for supply-related metrics."""

    def test_tokenomics_risk_calculates_circulating_ratio(self) -> None:
        data = {
            "circulating_supply": 600_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,
        }
        result = TokenomicsRisk.analyze(data)
        assert abs(result.circulating_ratio - 0.6) < 0.001

    def test_tokenomics_risk_low_circulating_ratio_increases_risk(self) -> None:
        """Low circulating ratio (more locked supply) = more risk."""
        high_circ = {
            "circulating_supply": 900_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,
        }
        low_circ = {
            "circulating_supply": 200_000.0,
            "total_supply": 1_000_000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,
        }

        high_result = TokenomicsRisk.analyze(high_circ)
        low_result = TokenomicsRisk.analyze(low_circ)
        assert low_result.risk_score > high_result.risk_score


class TestTokenomicsRiskValidation:
    """TokenomicsRisk validates input data."""

    def test_tokenomics_risk_raises_on_missing_fields(self) -> None:
        from app.exceptions import ScoringError

        with pytest.raises(ScoringError):
            TokenomicsRisk.analyze({})

    def test_tokenomics_risk_raises_on_zero_total_supply(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "circulating_supply": 1000.0,
            "total_supply": 0.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,
        }
        with pytest.raises(ScoringError):
            TokenomicsRisk.analyze(data)

    def test_tokenomics_risk_raises_on_negative_inflation(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "circulating_supply": 1000.0,
            "total_supply": 2000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": -0.05,  # Negative invalid
        }
        with pytest.raises(ScoringError):
            TokenomicsRisk.analyze(data)

    def test_tokenomics_risk_raises_on_circulating_exceeds_total(self) -> None:
        from app.exceptions import ScoringError

        data = {
            "circulating_supply": 2000.0,  # More than total
            "total_supply": 1000.0,
            "unlock_schedule": [],
            "annual_inflation_rate": 0.02,
        }
        with pytest.raises(ScoringError):
            TokenomicsRisk.analyze(data)
