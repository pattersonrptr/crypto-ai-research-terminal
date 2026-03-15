"""Tests for daily digest generation — Phase 11.

The digest summarises the day's alerts into a single DAILY_REPORT alert
and optionally sends it via Telegram.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.alerts.alert_formatter import AlertType
from app.models.alert import Alert


def _fake_alert(
    alert_type: str = "listing_candidate",
    symbol: str = "BTC",
) -> Alert:
    """Create a minimal Alert for testing."""
    a = Alert(
        token_id=1,
        alert_type=alert_type,
        message=f"{symbol}: test alert",
        token_symbol=symbol,
    )
    a.triggered_at = datetime.now(UTC)  # type: ignore[assignment]
    return a


class TestDailyDigest:
    """Tests for build_daily_digest and send_daily_digest."""

    def test_build_digest_from_alerts(self) -> None:
        """Digest must produce a DAILY_REPORT alert summarising the day's alerts."""
        from app.scheduler.digest import build_daily_digest

        alerts = [
            _fake_alert("listing_candidate", "AAA"),
            _fake_alert("rugpull_risk", "BBB"),
            _fake_alert("listing_candidate", "CCC"),
        ]
        digest = build_daily_digest(alerts)

        assert digest.alert_type == AlertType.DAILY_REPORT.value
        assert digest.token_id is None
        assert "3" in digest.message  # mentions count
        assert "listing_candidate" in digest.message

    def test_build_digest_empty_alerts(self) -> None:
        """Digest for zero alerts should still produce a DAILY_REPORT."""
        from app.scheduler.digest import build_daily_digest

        digest = build_daily_digest([])
        assert digest.alert_type == AlertType.DAILY_REPORT.value
        assert "0" in digest.message

    def test_digest_metadata_has_breakdown(self) -> None:
        """Digest alert_metadata should contain per-type counts."""
        from app.scheduler.digest import build_daily_digest

        alerts = [
            _fake_alert("listing_candidate", "A"),
            _fake_alert("listing_candidate", "B"),
            _fake_alert("rugpull_risk", "C"),
        ]
        digest = build_daily_digest(alerts)
        assert digest.alert_metadata is not None
        assert digest.alert_metadata["by_type"]["listing_candidate"] == 2
        assert digest.alert_metadata["by_type"]["rugpull_risk"] == 1

    @pytest.mark.asyncio
    async def test_send_daily_digest_calls_telegram(self) -> None:
        """send_daily_digest should format and send via TelegramBot."""
        from app.scheduler.digest import send_daily_digest

        alerts = [_fake_alert("listing_candidate", "BTC")]

        with patch("app.scheduler.digest.TelegramBot") as mock_bot_cls:
            mock_bot = AsyncMock()
            mock_bot.send_message.return_value = True
            mock_bot_cls.return_value.__aenter__ = AsyncMock(return_value=mock_bot)
            mock_bot_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_daily_digest(
                alerts,
                telegram_token="fake-token",
                chat_id="123",
            )

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_daily_digest_skips_when_no_token(self) -> None:
        """send_daily_digest should skip Telegram when token is empty."""
        from app.scheduler.digest import send_daily_digest

        result = await send_daily_digest(
            [_fake_alert()],
            telegram_token="",
            chat_id="123",
        )
        assert result is False
