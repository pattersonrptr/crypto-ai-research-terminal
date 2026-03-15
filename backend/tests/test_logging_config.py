"""Tests for the structlog logging configuration module.

Verifies that configure_logging() sets up structlog with the correct
processors for dev (console) and production (JSON) modes.
"""

from __future__ import annotations

import json
import logging

import structlog

from app.logging_config import configure_logging


class TestConfigureLogging:
    """configure_logging() sets up structlog correctly."""

    def test_configure_logging_dev_mode_runs_without_error(self) -> None:
        """Dev mode should configure structlog without raising."""
        configure_logging(json_output=False, log_level="DEBUG")
        logger = structlog.get_logger("test")
        # Smoke test — should not raise
        assert logger is not None

    def test_configure_logging_json_mode_runs_without_error(self) -> None:
        """JSON mode should configure structlog without raising."""
        configure_logging(json_output=True, log_level="INFO")
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_configure_logging_sets_log_level(self) -> None:
        """The root logger level should be set to the requested level."""
        configure_logging(json_output=False, log_level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_configure_logging_json_output_produces_valid_json(self, capsys) -> None:  # type: ignore[no-untyped-def]
        """In JSON mode, log output should be parseable as JSON."""
        configure_logging(json_output=True, log_level="INFO")
        logger = structlog.get_logger("json_test")
        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        lines = [ln.strip() for ln in captured.out.strip().split("\n") if ln.strip()]
        # The JSON line should be among the captured output
        found_json = False
        for line in lines:
            try:
                data = json.loads(line)
                if data.get("event") == "test_event":
                    assert data["key"] == "value"
                    found_json = True
                    break
            except json.JSONDecodeError:
                continue
        assert found_json, f"No valid JSON line found in output: {captured.out}"

    def test_configure_logging_default_is_info(self) -> None:
        """Default log level should be INFO."""
        configure_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO
