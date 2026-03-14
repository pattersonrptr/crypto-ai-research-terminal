"""Tests for AlertFormatter — formats alerts for Telegram delivery."""

from datetime import UTC, datetime

import pytest

from app.alerts.alert_formatter import AlertFormatter, AlertType, FormattedAlert


class TestAlertFormatterInit:
    """Test AlertFormatter initialization."""

    def test_init_creates_formatter(self) -> None:
        """AlertFormatter can be instantiated."""
        formatter = AlertFormatter()
        assert formatter is not None

    def test_formatter_has_format_method(self) -> None:
        """AlertFormatter has a format method."""
        formatter = AlertFormatter()
        assert hasattr(formatter, "format")
        assert callable(formatter.format)


class TestAlertType:
    """Test AlertType enumeration."""

    def test_alert_type_listing_candidate(self) -> None:
        """LISTING_CANDIDATE alert type exists."""
        assert AlertType.LISTING_CANDIDATE.value == "listing_candidate"

    def test_alert_type_whale_accumulation(self) -> None:
        """WHALE_ACCUMULATION alert type exists."""
        assert AlertType.WHALE_ACCUMULATION.value == "whale_accumulation"

    def test_alert_type_rugpull_risk(self) -> None:
        """RUGPULL_RISK alert type exists."""
        assert AlertType.RUGPULL_RISK.value == "rugpull_risk"

    def test_alert_type_manipulation_detected(self) -> None:
        """MANIPULATION_DETECTED alert type exists."""
        assert AlertType.MANIPULATION_DETECTED.value == "manipulation_detected"

    def test_alert_type_token_unlock(self) -> None:
        """TOKEN_UNLOCK_SOON alert type exists."""
        assert AlertType.TOKEN_UNLOCK_SOON.value == "token_unlock_soon"

    def test_alert_type_narrative_emerging(self) -> None:
        """NARRATIVE_EMERGING alert type exists."""
        assert AlertType.NARRATIVE_EMERGING.value == "narrative_emerging"

    def test_alert_type_memecoin_hype(self) -> None:
        """MEMECOIN_HYPE_DETECTED alert type exists."""
        assert AlertType.MEMECOIN_HYPE_DETECTED.value == "memecoin_hype_detected"

    def test_alert_type_daily_report(self) -> None:
        """DAILY_REPORT alert type exists."""
        assert AlertType.DAILY_REPORT.value == "daily_report"


class TestFormattedAlert:
    """Test FormattedAlert dataclass."""

    def test_formatted_alert_has_required_fields(self) -> None:
        """FormattedAlert has title, body, and emoji fields."""
        alert = FormattedAlert(
            title="Test Alert",
            body="This is a test",
            emoji="🚨",
            alert_type=AlertType.LISTING_CANDIDATE,
        )
        assert alert.title == "Test Alert"
        assert alert.body == "This is a test"
        assert alert.emoji == "🚨"
        assert alert.alert_type == AlertType.LISTING_CANDIDATE

    def test_formatted_alert_to_telegram_message(self) -> None:
        """FormattedAlert can be converted to Telegram message format."""
        alert = FormattedAlert(
            title="Test Alert",
            body="Line 1\nLine 2",
            emoji="🚨",
            alert_type=AlertType.LISTING_CANDIDATE,
        )
        message = alert.to_telegram()
        assert "🚨" in message
        assert "Test Alert" in message
        assert "Line 1" in message
        assert "Line 2" in message


class TestFormatListingCandidate:
    """Test formatting of LISTING_CANDIDATE alerts."""

    def test_format_listing_candidate_basic(self) -> None:
        """Format a basic listing candidate alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "ABC",
            "name": "ABC Token",
            "listing_score": 82,
            "signals": [
                "DEX volume grew 340% in 7 days",
                "Holders grew 28% in 7 days",
                "Social mentions +180%",
            ],
            "probability": "high",
            "likely_exchanges": ["Binance", "KuCoin"],
        }
        result = formatter.format(AlertType.LISTING_CANDIDATE, data)

        assert isinstance(result, FormattedAlert)
        assert result.alert_type == AlertType.LISTING_CANDIDATE
        assert "ABC" in result.body
        assert "82" in result.body
        assert "Binance" in result.body

    def test_format_listing_candidate_contains_disclaimer(self) -> None:
        """Listing candidate alert contains disclaimer."""
        formatter = AlertFormatter()
        data = {
            "symbol": "XYZ",
            "name": "XYZ Token",
            "listing_score": 75,
            "signals": ["Volume spike detected"],
            "probability": "medium",
            "likely_exchanges": ["Kraken"],
        }
        result = formatter.format(AlertType.LISTING_CANDIDATE, data)
        telegram_msg = result.to_telegram()

        assert "Not a guarantee" in telegram_msg or "DYOR" in telegram_msg


class TestFormatWhaleAccumulation:
    """Test formatting of WHALE_ACCUMULATION alerts."""

    def test_format_whale_accumulation(self) -> None:
        """Format a whale accumulation alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "SOL",
            "name": "Solana",
            "whale_score": 7.5,
            "top10_change_pct": 12.5,
            "large_transactions": 3,
            "period_days": 7,
        }
        result = formatter.format(AlertType.WHALE_ACCUMULATION, data)

        assert isinstance(result, FormattedAlert)
        assert "SOL" in result.body
        assert "whale" in result.body.lower() or "🐋" in result.emoji


class TestFormatRugpullRisk:
    """Test formatting of RUGPULL_RISK alerts."""

    def test_format_rugpull_risk(self) -> None:
        """Format a rugpull risk alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "SCAM",
            "name": "Scam Token",
            "risk_score": 0.85,
            "risk_factors": [
                "Anonymous team",
                "Wallet concentration >50%",
                "No audit",
            ],
        }
        result = formatter.format(AlertType.RUGPULL_RISK, data)

        assert isinstance(result, FormattedAlert)
        assert "SCAM" in result.body
        assert "Anonymous" in result.body or "risk" in result.body.lower()


class TestFormatManipulationDetected:
    """Test formatting of MANIPULATION_DETECTED alerts."""

    def test_format_manipulation_detected(self) -> None:
        """Format a manipulation detected alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "PUMP",
            "name": "Pump Token",
            "manipulation_type": "pump_and_dump",
            "confidence": 0.78,
            "indicators": ["Price spike >200%", "Crash >50% within 24h"],
        }
        result = formatter.format(AlertType.MANIPULATION_DETECTED, data)

        assert isinstance(result, FormattedAlert)
        assert "PUMP" in result.body


class TestFormatTokenUnlock:
    """Test formatting of TOKEN_UNLOCK_SOON alerts."""

    def test_format_token_unlock(self) -> None:
        """Format a token unlock alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "LOCK",
            "name": "Lock Token",
            "unlock_pct": 8.5,
            "unlock_date": datetime(2026, 3, 20, tzinfo=UTC),
            "unlock_usd_value": 15_000_000,
        }
        result = formatter.format(AlertType.TOKEN_UNLOCK_SOON, data)

        assert isinstance(result, FormattedAlert)
        assert "LOCK" in result.body
        assert "8.5" in result.body or "8,5" in result.body


class TestFormatNarrativeEmerging:
    """Test formatting of NARRATIVE_EMERGING alerts."""

    def test_format_narrative_emerging(self) -> None:
        """Format a narrative emerging alert."""
        formatter = AlertFormatter()
        data = {
            "narrative": "AI Agents",
            "momentum_score": 8.2,
            "top_tokens": ["AGIX", "FET", "OCEAN"],
            "mention_growth_pct": 340,
        }
        result = formatter.format(AlertType.NARRATIVE_EMERGING, data)

        assert isinstance(result, FormattedAlert)
        assert "AI Agents" in result.body
        assert "AGIX" in result.body or "FET" in result.body


class TestFormatDailyReport:
    """Test formatting of DAILY_REPORT alerts."""

    def test_format_daily_report(self) -> None:
        """Format a daily report alert."""
        formatter = AlertFormatter()
        data = {
            "date": datetime(2026, 3, 13, tzinfo=UTC),
            "top_opportunities": [
                {"symbol": "ARB", "score": 0.88},
                {"symbol": "SOL", "score": 0.85},
                {"symbol": "ETH", "score": 0.82},
            ],
            "active_alerts_count": 5,
            "market_sentiment": "bullish",
        }
        result = formatter.format(AlertType.DAILY_REPORT, data)

        assert isinstance(result, FormattedAlert)
        assert "ARB" in result.body
        assert result.alert_type == AlertType.DAILY_REPORT


class TestFormatMemecoinHype:
    """Test formatting of MEMECOIN_HYPE_DETECTED alerts."""

    def test_format_memecoin_hype(self) -> None:
        """Format a memecoin hype alert."""
        formatter = AlertFormatter()
        data = {
            "symbol": "PEPE",
            "name": "Pepe",
            "social_growth_pct": 850,
            "volume_growth_pct": 1200,
            "holder_growth_pct": 45,
        }
        result = formatter.format(AlertType.MEMECOIN_HYPE_DETECTED, data)

        assert isinstance(result, FormattedAlert)
        assert "PEPE" in result.body


class TestFormatterEdgeCases:
    """Test edge cases and error handling."""

    def test_format_unknown_alert_type_raises_error(self) -> None:
        """Formatting an unknown alert type raises ValueError."""
        formatter = AlertFormatter()
        with pytest.raises(ValueError, match="Unknown alert type"):
            formatter.format("invalid_type", {})  # type: ignore

    def test_format_missing_required_field_raises_error(self) -> None:
        """Missing required field raises KeyError."""
        formatter = AlertFormatter()
        with pytest.raises(KeyError):
            formatter.format(AlertType.LISTING_CANDIDATE, {"symbol": "ABC"})

    def test_format_empty_signals_list(self) -> None:
        """Empty signals list is handled gracefully."""
        formatter = AlertFormatter()
        data = {
            "symbol": "ABC",
            "name": "ABC Token",
            "listing_score": 50,
            "signals": [],
            "probability": "low",
            "likely_exchanges": [],
        }
        result = formatter.format(AlertType.LISTING_CANDIDATE, data)
        assert isinstance(result, FormattedAlert)
