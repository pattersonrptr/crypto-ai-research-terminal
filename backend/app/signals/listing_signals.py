"""ListingSignals — generates signals from exchange listing events.

Processes listing changes to create actionable signals:
- Assigns strength based on exchange tier
- Aggregates multiple listings for same token
- Calculates listing velocity
"""

from collections import defaultdict
from dataclasses import dataclass

from app.collectors.exchange_monitor import ListingChange


@dataclass(frozen=True)
class ListingSignal:
    """Signal generated from a listing event."""

    token: str
    signal_type: str  # "new_listing"
    strength: float  # 0.0 to 1.0
    exchange_count: int
    exchanges: frozenset[str]


# Exchange tier classification for signal strength
_TIER1_EXCHANGES = {"binance", "coinbase", "okx", "bybit"}
_TIER2_EXCHANGES = {"kraken", "kucoin", "htx", "gate", "bitfinex", "bitstamp"}

# Base strength by tier
_TIER1_STRENGTH = 0.8
_TIER2_STRENGTH = 0.5
_TIER3_STRENGTH = 0.2

# Bonus for multiple exchange listings
_MULTI_EXCHANGE_BONUS = 0.1


class ListingSignals:
    """Generates listing signals from exchange listing changes."""

    @staticmethod
    def _get_exchange_strength(exchange: str) -> float:
        """Get base strength for an exchange based on tier."""
        exchange_lower = exchange.lower()
        if exchange_lower in _TIER1_EXCHANGES:
            return _TIER1_STRENGTH
        if exchange_lower in _TIER2_EXCHANGES:
            return _TIER2_STRENGTH
        return _TIER3_STRENGTH

    @classmethod
    def from_changes(cls, changes: list[ListingChange]) -> list[ListingSignal]:
        """Generate signals from listing changes.

        Args:
            changes: List of ListingChange events from ExchangeMonitor.

        Returns:
            List of ListingSignal, one per token (aggregated).
        """
        if not changes:
            return []

        # Filter to only new listings
        listings = [c for c in changes if c.change_type == "listed"]
        if not listings:
            return []

        # Aggregate by token
        token_exchanges: dict[str, set[str]] = defaultdict(set)
        for listing in listings:
            token_exchanges[listing.token].add(listing.exchange)

        signals = []
        for token, exchanges in token_exchanges.items():
            # Calculate strength: max exchange strength + bonus for multiple
            exchange_strengths = [cls._get_exchange_strength(ex) for ex in exchanges]
            base_strength = max(exchange_strengths)

            # Add bonus for each additional exchange (capped at 1.0)
            bonus = (len(exchanges) - 1) * _MULTI_EXCHANGE_BONUS
            total_strength = min(base_strength + bonus, 1.0)

            signals.append(
                ListingSignal(
                    token=token,
                    signal_type="new_listing",
                    strength=total_strength,
                    exchange_count=len(exchanges),
                    exchanges=frozenset(exchanges),
                )
            )

        return signals

    @staticmethod
    def calculate_velocity(total_listings: int, days: int) -> float:
        """Calculate listing velocity (listings per day).

        Args:
            total_listings: Number of new listings in the period.
            days: Time period in days.

        Returns:
            Listings per day rate.
        """
        if days <= 0 or total_listings <= 0:
            return 0.0
        return total_listings / days
