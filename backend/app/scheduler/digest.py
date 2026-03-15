"""Daily digest — summarise the day's alerts into a single DAILY_REPORT.

Optionally sends the digest via Telegram.
"""

from __future__ import annotations

from collections import Counter

import structlog

from app.alerts.alert_formatter import AlertType
from app.alerts.telegram_bot import TelegramBot
from app.models.alert import Alert

logger = structlog.get_logger(__name__)


def build_daily_digest(alerts: list[Alert]) -> Alert:
    """Build a DAILY_REPORT alert summarising today's alerts.

    Args:
        alerts: List of Alert ORM objects triggered today.

    Returns:
        A new (unpersisted) Alert with type DAILY_REPORT.
    """
    total = len(alerts)
    by_type: dict[str, int] = dict(Counter(a.alert_type for a in alerts))

    # Build a human-readable summary
    if total == 0:
        body = "📊 Daily Digest: 0 alerts triggered today. All clear!"
    else:
        lines = [f"📊 Daily Digest: {total} alert(s) triggered today."]
        for atype, count in sorted(by_type.items()):
            lines.append(f"  • {atype}: {count}")
        body = "\n".join(lines)

    return Alert(
        token_id=None,
        token_symbol=None,
        alert_type=AlertType.DAILY_REPORT.value,
        message=body,
        alert_metadata={"total": total, "by_type": by_type},
    )


async def send_daily_digest(
    alerts: list[Alert],
    *,
    telegram_token: str = "",
    chat_id: str = "",
) -> bool:
    """Build digest and send it via Telegram if configured.

    Args:
        alerts: Today's triggered alerts.
        telegram_token: Telegram bot token (empty = skip).
        chat_id: Telegram chat ID.

    Returns:
        True if the message was sent, False if skipped or failed.
    """
    if not telegram_token or not chat_id:
        logger.info("send_daily_digest.skipped", reason="telegram_not_configured")
        return False

    digest = build_daily_digest(alerts)

    try:
        async with TelegramBot(token=telegram_token, chat_id=chat_id) as bot:
            success = await bot.send_message(digest.message)
        if success:
            logger.info("send_daily_digest.sent", total=len(alerts))
        return success
    except Exception:
        logger.exception("send_daily_digest.error")
        return False
