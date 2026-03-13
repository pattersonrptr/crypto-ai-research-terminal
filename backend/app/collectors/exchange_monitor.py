"""ExchangeMonitor — tracks token listings across exchanges.

Provides:
- Snapshot of current listings per exchange
- Diff detection for new listings and delistings
- Token-to-exchange mapping for listing breadth analysis
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ListingChange:
    """Represents a listing or delisting event."""

    token: str
    exchange: str
    change_type: Literal["listed", "delisted"]


@dataclass
class ListingSnapshot:
    """Point-in-time snapshot of exchange listings."""

    # Exchange -> set of tokens listed
    exchange_tokens: dict[str, set[str]] = field(default_factory=dict)
    # Token -> set of exchanges where it's listed
    token_exchanges: dict[str, set[str]] = field(default_factory=dict)


class ExchangeMonitor:
    """Monitors exchange listings and detects changes."""

    @staticmethod
    def get_snapshot(exchange_data: dict[str, list[str]]) -> ListingSnapshot:
        """Create a listing snapshot from exchange data.

        Args:
            exchange_data: Dict mapping exchange name to list of tokens.
                Example: {"binance": ["BTC", "ETH"], "coinbase": ["BTC"]}

        Returns:
            ListingSnapshot with bidirectional mappings.
        """
        snapshot = ListingSnapshot()

        for exchange, tokens in exchange_data.items():
            token_set = set(tokens)
            snapshot.exchange_tokens[exchange] = token_set

            for token in token_set:
                if token not in snapshot.token_exchanges:
                    snapshot.token_exchanges[token] = set()
                snapshot.token_exchanges[token].add(exchange)

        return snapshot

    @staticmethod
    def diff(old: ListingSnapshot, new: ListingSnapshot) -> list[ListingChange]:
        """Calculate listing changes between two snapshots.

        Args:
            old: Previous snapshot.
            new: Current snapshot.

        Returns:
            List of ListingChange events (new listings and delistings).
        """
        changes: list[ListingChange] = []

        # Get all exchanges from both snapshots
        all_exchanges = set(old.exchange_tokens.keys()) | set(new.exchange_tokens.keys())

        for exchange in all_exchanges:
            old_tokens = old.exchange_tokens.get(exchange, set())
            new_tokens = new.exchange_tokens.get(exchange, set())

            # New listings: in new but not in old
            for token in new_tokens - old_tokens:
                changes.append(ListingChange(token=token, exchange=exchange, change_type="listed"))

            # Delistings: in old but not in new
            for token in old_tokens - new_tokens:
                changes.append(
                    ListingChange(token=token, exchange=exchange, change_type="delisted")
                )

        return changes

    @staticmethod
    def count_exchanges(snapshot: ListingSnapshot, token: str) -> int:
        """Count how many exchanges list a given token.

        Args:
            snapshot: Current listing snapshot.
            token: Token symbol to look up.

        Returns:
            Number of exchanges where the token is listed.
        """
        return len(snapshot.token_exchanges.get(token, set()))
