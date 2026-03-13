"""Tests for TelegramBot — sends alerts via Telegram Bot API.

TDD RED phase: Tests written before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.alerts.alert_formatter import AlertType, FormattedAlert
from app.alerts.telegram_bot import TelegramBot, TelegramBotError


class TestTelegramBotInit:
    """Test TelegramBot initialization."""

    def test_init_with_token_and_chat_id(self) -> None:
        """TelegramBot initializes with token and chat_id."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert bot is not None
        assert bot.chat_id == "12345"

    def test_init_requires_token(self) -> None:
        """TelegramBot raises error without token."""
        with pytest.raises(ValueError, match="token"):
            TelegramBot(token="", chat_id="12345")

    def test_init_requires_chat_id(self) -> None:
        """TelegramBot raises error without chat_id."""
        with pytest.raises(ValueError, match="chat_id"):
            TelegramBot(token="test_token", chat_id="")


class TestTelegramBotMethods:
    """Test TelegramBot has required methods."""

    def test_bot_has_send_message_method(self) -> None:
        """TelegramBot has async send_message method."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert hasattr(bot, "send_message")
        assert callable(bot.send_message)

    def test_bot_has_send_alert_method(self) -> None:
        """TelegramBot has async send_alert method."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert hasattr(bot, "send_alert")
        assert callable(bot.send_alert)

    def test_bot_has_close_method(self) -> None:
        """TelegramBot has async close method."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert hasattr(bot, "close")
        assert callable(bot.close)


class TestSendMessage:
    """Test TelegramBot.send_message method."""

    @pytest.mark.asyncio
    async def test_send_message_makes_api_call(self) -> None:
        """send_message makes HTTP POST to Telegram API."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        with patch.object(bot, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await bot.send_message("Test message")

            mock_client.post.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(self) -> None:
        """send_message sends with Markdown parse mode by default."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        with patch.object(bot, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
            mock_client.post = AsyncMock(return_value=mock_response)

            await bot.send_message("*Bold* message")

            call_args = mock_client.post.call_args
            assert "parse_mode" in str(call_args) or call_args[1].get("json", {}).get("parse_mode") == "Markdown"

    @pytest.mark.asyncio
    async def test_send_message_returns_false_on_error(self) -> None:
        """send_message returns False on API error."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        with patch.object(bot, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"ok": False, "description": "Bad Request"}
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await bot.send_message("Test message")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_handles_network_error(self) -> None:
        """send_message handles network errors gracefully."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        with patch.object(bot, "_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))

            result = await bot.send_message("Test message")

            assert result is False


class TestSendAlert:
    """Test TelegramBot.send_alert method."""

    @pytest.mark.asyncio
    async def test_send_alert_formats_and_sends(self) -> None:
        """send_alert converts FormattedAlert to message and sends."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        alert = FormattedAlert(
            title="TEST ALERT",
            body="Test body",
            emoji="🚨",
            alert_type=AlertType.LISTING_CANDIDATE,
        )

        with patch.object(bot, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await bot.send_alert(alert)

            mock_send.assert_called_once()
            call_text = mock_send.call_args[0][0]
            assert "TEST ALERT" in call_text
            assert "Test body" in call_text
            assert "🚨" in call_text
            assert result is True

    @pytest.mark.asyncio
    async def test_send_alert_returns_false_on_failure(self) -> None:
        """send_alert returns False if send_message fails."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        alert = FormattedAlert(
            title="TEST",
            body="Body",
            emoji="⚠️",
            alert_type=AlertType.RUGPULL_RISK,
        )

        with patch.object(bot, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False

            result = await bot.send_alert(alert)

            assert result is False


class TestTelegramBotRateLimiting:
    """Test TelegramBot rate limiting."""

    def test_bot_has_rate_limit_property(self) -> None:
        """TelegramBot has rate_limit property."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert hasattr(bot, "rate_limit")

    def test_bot_default_rate_limit(self) -> None:
        """Default rate limit is 30 messages per second (Telegram limit)."""
        bot = TelegramBot(token="test_token", chat_id="12345")
        assert bot.rate_limit == 30

    def test_bot_custom_rate_limit(self) -> None:
        """Custom rate limit can be set."""
        bot = TelegramBot(token="test_token", chat_id="12345", rate_limit=10)
        assert bot.rate_limit == 10


class TestTelegramBotContextManager:
    """Test TelegramBot as async context manager."""

    @pytest.mark.asyncio
    async def test_bot_as_context_manager(self) -> None:
        """TelegramBot can be used as async context manager."""
        async with TelegramBot(token="test_token", chat_id="12345") as bot:
            assert bot is not None

    @pytest.mark.asyncio
    async def test_bot_close_is_called_on_exit(self) -> None:
        """close() is called when exiting context."""
        bot = TelegramBot(token="test_token", chat_id="12345")

        with patch.object(bot, "close", new_callable=AsyncMock) as mock_close:
            async with bot:
                pass

            mock_close.assert_called_once()


class TestTelegramBotError:
    """Test TelegramBotError exception."""

    def test_telegram_bot_error_is_exception(self) -> None:
        """TelegramBotError is an Exception."""
        error = TelegramBotError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_telegram_bot_error_with_response_code(self) -> None:
        """TelegramBotError can include response code."""
        error = TelegramBotError("API error", status_code=400)
        assert error.status_code == 400
