"""Tests: collect_twitter_data must skip immediately when credentials are empty.

When TWITTER_USERNAME / TWITTER_EMAIL / TWITTER_PASSWORD are blank (the default),
the pipeline should NOT instantiate TwitterTwikitCollector at all — it should
return an empty dict immediately and log an informative skip message.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.scheduler.jobs import collect_twitter_data

# The collector is imported lazily inside the function, so we patch at the source.
_COLLECTOR_CLS_PATH = "app.collectors.twitter_twikit_collector.TwitterTwikitCollector"


class TestTwitterSkipEmptyCredentials:
    """collect_twitter_data short-circuits when Twitter credentials are missing."""

    @pytest.mark.asyncio
    async def test_collect_twitter_data_skips_when_credentials_empty(self) -> None:
        """Must return {} immediately without creating a collector."""
        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            mock_settings_cls.return_value.twitter_username = ""
            mock_settings_cls.return_value.twitter_email = ""
            mock_settings_cls.return_value.twitter_password = ""

            with patch(_COLLECTOR_CLS_PATH) as mock_collector_cls:
                result = await collect_twitter_data(symbols=["BTC", "ETH"])

        assert result == {}
        mock_collector_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_twitter_data_skips_when_username_only_missing(self) -> None:
        """Even if email+password set, missing username means skip."""
        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            mock_settings_cls.return_value.twitter_username = ""
            mock_settings_cls.return_value.twitter_email = "test@example.com"
            mock_settings_cls.return_value.twitter_password = "secret"

            with patch(_COLLECTOR_CLS_PATH) as mock_collector_cls:
                result = await collect_twitter_data(symbols=["BTC"])

        assert result == {}
        mock_collector_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_twitter_data_logs_skip_reason(self) -> None:
        """Must log an informative message when skipping due to empty creds."""
        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            mock_settings_cls.return_value.twitter_username = ""
            mock_settings_cls.return_value.twitter_email = ""
            mock_settings_cls.return_value.twitter_password = ""

            with patch("app.scheduler.jobs.logger") as mock_logger:
                await collect_twitter_data(symbols=["BTC"])

        mock_logger.info.assert_any_call(
            "collect_twitter_data.skipped",
            reason="twitter credentials not configured",
        )


class TestTwitterUsesSettingsCredentials:
    """When credentials ARE configured, they must be passed to the collector."""

    @pytest.mark.asyncio
    async def test_collect_twitter_data_passes_credentials_from_settings(self) -> None:
        """Must forward username/email/password from Settings to collector."""
        mock_collector_instance = AsyncMock()
        mock_collector_instance.collect_mentions.return_value = {
            "symbol": "BTC",
            "mention_count": 42,
            "total_engagement": 100,
            "texts": [],
        }

        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            mock_settings_cls.return_value.twitter_username = "myuser"
            mock_settings_cls.return_value.twitter_email = "me@example.com"
            mock_settings_cls.return_value.twitter_password = "s3cret"

            with patch(
                _COLLECTOR_CLS_PATH,
                return_value=mock_collector_instance,
            ) as mock_collector_cls:
                result = await collect_twitter_data(symbols=["BTC"])

        mock_collector_cls.assert_called_once_with(
            username="myuser",
            email="me@example.com",
            password="s3cret",
        )
        assert "BTC" in result

    @pytest.mark.asyncio
    async def test_collect_twitter_data_reuses_single_collector_for_all_symbols(
        self,
    ) -> None:
        """Must create ONE collector and reuse it across all symbols."""
        mock_collector_instance = AsyncMock()
        mock_collector_instance.collect_mentions.return_value = {
            "symbol": "X",
            "mention_count": 1,
            "total_engagement": 0,
            "texts": [],
        }

        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            mock_settings_cls.return_value.twitter_username = "usr"
            mock_settings_cls.return_value.twitter_email = "e@x.com"
            mock_settings_cls.return_value.twitter_password = "pw"

            with patch(
                _COLLECTOR_CLS_PATH,
                return_value=mock_collector_instance,
            ) as mock_collector_cls:
                result = await collect_twitter_data(symbols=["BTC", "ETH", "SOL"])

        # Collector instantiated only once
        assert mock_collector_cls.call_count == 1
        # Login called only once
        mock_collector_instance.login.assert_awaited_once()
        # collect_mentions called for each symbol
        assert mock_collector_instance.collect_mentions.await_count == 3
        assert len(result) == 3


class TestTwitterCollectorInjectionStillWorks:
    """Pre-built twitter_collector param must bypass settings + instantiation."""

    @pytest.mark.asyncio
    async def test_collect_twitter_data_with_injected_collector_ignores_settings(
        self,
    ) -> None:
        """When twitter_collector is passed, Settings is not consulted."""
        mock_collector = AsyncMock()
        mock_collector.collect_mentions.return_value = {
            "symbol": "BTC",
            "mention_count": 5,
            "total_engagement": 10,
            "texts": [],
        }

        with patch("app.scheduler.jobs.Settings") as mock_settings_cls:
            result = await collect_twitter_data(
                symbols=["BTC"],
                twitter_collector=mock_collector,
            )

        # Settings should NOT be instantiated when collector is injected
        mock_settings_cls.assert_not_called()
        mock_collector.collect_mentions.assert_awaited_once_with("BTC")
        assert "BTC" in result
