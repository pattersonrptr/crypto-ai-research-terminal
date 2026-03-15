"""Logging configuration — structlog with JSON or console rendering.

Call :func:`configure_logging` once at application startup (before any
logger is used) to set up structlog and the standard-library root logger.

**Dev mode** (``json_output=False``)
    Pretty-printed colourised console output via ``ConsoleRenderer``.

**Production mode** (``json_output=True``)
    Structured JSON output on every log line, suitable for ingestion
    by Loki, Grafana, CloudWatch, or any JSON-aware log shipper.

Log rotation is handled at the infrastructure level:
- Docker: use ``json-file`` log driver with ``max-size`` / ``max-file``
  (see docker-compose.yml).
- Bare-metal: use logrotate or redirect stdout to a file with rotation.

Usage::

    from app.logging_config import configure_logging

    configure_logging(json_output=True, log_level="INFO")
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(
    *,
    json_output: bool = False,
    log_level: str = "INFO",
) -> None:
    """Configure structlog and standard-library logging.

    Args:
        json_output: If True, render logs as JSON (for production / log
                     shippers).  If False, use colourised console output.
        log_level: Root logger level.  One of DEBUG, INFO, WARNING, ERROR,
                   CRITICAL.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Standard-library logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,
    )

    # Shared processors (applied before rendering)
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # Production: JSON lines to stdout
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: pretty colourised console
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Attach a ProcessorFormatter to the root handler so structlog events
    # flow through standard-library logging (needed for JSON output)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(formatter)
