"""TelegramBot — sends alerts via Telegram Bot API.

Provides async interface for sending formatted alerts to Telegram
with rate limiting and error handling.
"""

from typing import TYPE_CHECKING

import httpx
import structlog

if TYPE_CHECKING:
    from app.alerts.alert_formatter import FormattedAlert

logger = structlog.get_logger(__name__)

# Telegram Bot API base URL
TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramBotError(Exception):
    """Exception raised for Telegram Bot API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the error.

        Args:
            message: Error message.
            status_code: Optional HTTP status code from API response.
        """
        super().__init__(message)
        self.status_code = status_code


class TelegramBot:
    """Async Telegram Bot client for sending alerts."""

    def __init__(
        self,
        token: str,
        chat_id: str,
        rate_limit: int = 30,
    ) -> None:
        """Initialize the Telegram bot.

        Args:
            token: Telegram Bot API token.
            chat_id: Target chat/channel ID.
            rate_limit: Max messages per second (default: 30, Telegram limit).

        Raises:
            ValueError: If token or chat_id is empty.
        """
        if not token:
            raise ValueError("token is required")
        if not chat_id:
            raise ValueError("chat_id is required")

        self._token = token
        self._chat_id = chat_id
        self._rate_limit = rate_limit
        self._client = httpx.AsyncClient(timeout=30.0)
        self._api_url = f"{TELEGRAM_API_BASE}{token}"

    @property
    def chat_id(self) -> str:
        """Return the configured chat ID."""
        return self._chat_id

    @property
    def rate_limit(self) -> int:
        """Return the rate limit (messages per second)."""
        return self._rate_limit

    async def send_message(
        self,
        text: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> bool:
        """Send a text message to the configured chat.

        Args:
            text: Message text (supports Markdown formatting).
            parse_mode: Parse mode for formatting (default: Markdown).
            disable_notification: If True, sends silently.

        Returns:
            True if message was sent successfully, False otherwise.
        """
        url = f"{self._api_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }

        try:
            response = await self._client.post(url, json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("ok"):
                logger.info(
                    "telegram_message_sent",
                    chat_id=self._chat_id,
                    message_id=data.get("result", {}).get("message_id"),
                )
                return True

            logger.warning(
                "telegram_api_error",
                status_code=response.status_code,
                description=data.get("description", "Unknown error"),
            )
            return False

        except Exception as e:
            logger.error(
                "telegram_send_failed",
                error=str(e),
                chat_id=self._chat_id,
            )
            return False

    async def send_alert(self, alert: "FormattedAlert") -> bool:
        """Send a formatted alert to Telegram.

        Args:
            alert: FormattedAlert instance to send.

        Returns:
            True if alert was sent successfully, False otherwise.
        """
        message = alert.to_telegram()
        return await self.send_message(message)

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._client.aclose()
        logger.debug("telegram_bot_closed")

    async def __aenter__(self) -> "TelegramBot":
        """Enter async context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context and close client."""
        await self.close()
