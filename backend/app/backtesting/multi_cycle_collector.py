"""Multi-cycle historical data collector.

Fetches monthly price/volume/market-cap snapshots from CoinGecko for all
tokens defined in :mod:`cycle_config` across multiple BTC market cycles.

The collector:
- Respects configurable delay between API requests (rate limiting).
- Parses CoinGecko ``/coins/{id}/market_chart/range`` responses using the
  existing ``historical_data_collector.parse_market_chart_to_snapshots``.
- Provides ``to_monthly()`` to reduce daily snapshots to one-per-month.
- Reports progress and handles partial failures gracefully.

This module is part of Phase 14 — Backtesting Multi-Cycle Validation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import structlog

from app.backtesting.cycle_config import get_cycle
from app.backtesting.historical_data_collector import (
    build_monthly_snapshots,
    parse_market_chart_to_snapshots,
)

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CollectionProgress:
    """Tracks collection progress for a single cycle.

    Args:
        cycle_name: The cycle being collected.
        total_tokens: Total tokens to collect.
        completed_tokens: Tokens successfully collected so far.
        failed_tokens: Tokens that failed collection.
    """

    cycle_name: str
    total_tokens: int
    completed_tokens: int
    failed_tokens: int

    @property
    def pct_complete(self) -> float:
        """Percentage of tokens processed (completed + failed)."""
        if self.total_tokens == 0:
            return 0.0
        return (self.completed_tokens + self.failed_tokens) / self.total_tokens * 100.0


@dataclass
class CollectionResult:
    """Result of collecting historical data for a single cycle.

    Args:
        cycle_name: The cycle that was collected.
        snapshots: All daily snapshots collected across all tokens.
        errors: Mapping of symbol → error message for failed tokens.
    """

    cycle_name: str
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def n_tokens_collected(self) -> int:
        """Number of unique tokens with at least one snapshot."""
        return len({s["symbol"] for s in self.snapshots})

    @property
    def is_complete(self) -> bool:
        """True if no errors occurred during collection."""
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class MultiCycleCollector:
    """Fetches historical CoinGecko data for all tokens in a market cycle.

    Args:
        delay_between_requests: Seconds to wait between API calls.
            CoinGecko free tier allows ~10-30 req/min.
    """

    def __init__(self, delay_between_requests: float = 6.0) -> None:
        self.delay_between_requests = delay_between_requests

    # ------------------------------------------------------------------
    # Low-level fetch (mocked in tests)
    # ------------------------------------------------------------------

    async def _fetch_market_chart(
        self,
        coingecko_id: str,
        from_ts: int,
        to_ts: int,
    ) -> dict[str, Any]:
        """Fetch /coins/{id}/market_chart/range from CoinGecko.

        Subclass or mock this method for testing. In production this
        delegates to :class:`CoinGeckoCollector`.

        Args:
            coingecko_id: CoinGecko API identifier.
            from_ts: Start timestamp (Unix seconds).
            to_ts: End timestamp (Unix seconds).

        Returns:
            Raw JSON dict with ``prices``, ``total_volumes``, ``market_caps``.
        """
        # Default implementation — override in production or mock in tests.
        # The real CoinGecko collector integration happens at the call
        # site, not here, to keep this module testable without HTTP deps.
        raise NotImplementedError(
            "Subclass MultiCycleCollector or mock _fetch_market_chart "
            "to provide a real CoinGecko HTTP backend."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect_token(
        self,
        symbol: str,
        coingecko_id: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Collect daily snapshots for a single token over a date range.

        Args:
            symbol: Token ticker.
            coingecko_id: CoinGecko API identifier.
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            List of snapshot dicts sorted by ``snapshot_date``.

        Raises:
            RuntimeError: If the API call fails.
        """
        from_ts = int(datetime.combine(start_date, datetime.min.time(), tzinfo=UTC).timestamp())
        to_ts = int(datetime.combine(end_date, datetime.min.time(), tzinfo=UTC).timestamp())

        payload = await self._fetch_market_chart(coingecko_id, from_ts, to_ts)
        snapshots = parse_market_chart_to_snapshots(symbol, payload)

        logger.info(
            "multi_cycle_collector.token_collected",
            symbol=symbol,
            n_snapshots=len(snapshots),
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )
        return snapshots

    async def collect_cycle(
        self,
        cycle_name: str,
    ) -> CollectionResult:
        """Collect daily snapshots for all tokens in a cycle.

        Iterates through the cycle's token list, fetching data for each
        with a configurable delay between requests. Partial failures are
        captured in ``errors`` but don't stop the collection.

        Args:
            cycle_name: The cycle identifier (e.g. ``"cycle_2_2019_2021"``).

        Returns:
            A :class:`CollectionResult` with all collected snapshots and
            any errors that occurred.

        Raises:
            KeyError: If the cycle name is not found.
        """
        cycle = get_cycle(cycle_name)
        result = CollectionResult(cycle_name=cycle_name)
        progress = CollectionProgress(
            cycle_name=cycle_name,
            total_tokens=len(cycle.tokens),
            completed_tokens=0,
            failed_tokens=0,
        )

        for i, token in enumerate(cycle.tokens):
            try:
                snaps = await self.collect_token(
                    symbol=token.symbol,
                    coingecko_id=token.coingecko_id,
                    start_date=cycle.bottom_date,
                    end_date=cycle.top_date,
                )
                result.snapshots.extend(snaps)
                progress.completed_tokens += 1
            except Exception as exc:
                result.errors[token.symbol] = str(exc)
                progress.failed_tokens += 1
                logger.warning(
                    "multi_cycle_collector.token_failed",
                    symbol=token.symbol,
                    error=str(exc),
                )

            # Rate limit delay (skip on last token)
            if self.delay_between_requests > 0 and i < len(cycle.tokens) - 1:
                await asyncio.sleep(self.delay_between_requests)

        logger.info(
            "multi_cycle_collector.cycle_complete",
            cycle=cycle_name,
            collected=progress.completed_tokens,
            failed=progress.failed_tokens,
            total_snapshots=len(result.snapshots),
        )
        return result

    @staticmethod
    def to_monthly(daily_snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reduce daily snapshots to one per month using earliest date.

        Delegates to :func:`build_monthly_snapshots`.

        Args:
            daily_snapshots: Daily snapshot dicts with ``snapshot_date``.

        Returns:
            Monthly snapshot dicts sorted by date ascending.
        """
        return build_monthly_snapshots(daily_snapshots)
