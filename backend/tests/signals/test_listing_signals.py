"""Tests for ListingSignals.

Generates listing signals based on exchange listing patterns:
- Detects tokens newly listed on major exchanges
- Assigns signal strength based on exchange tier
- Tracks listing velocity (rate of new listings)
"""

from app.collectors.exchange_monitor import ListingChange
from app.signals.listing_signals import ListingSignal, ListingSignals


class TestListingSignalsFromChanges:
    """ListingSignals.from_changes() generates signals from listing changes."""

    def test_listing_signals_from_changes_returns_signal_list(self) -> None:
        changes = [
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert isinstance(signals, list)
        assert all(isinstance(s, ListingSignal) for s in signals)

    def test_listing_signals_from_changes_creates_signal_for_new_listing(self) -> None:
        changes = [
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert len(signals) == 1
        assert signals[0].token == "SOL"
        assert signals[0].signal_type == "new_listing"

    def test_listing_signals_from_changes_ignores_delistings(self) -> None:
        """Delistings don't generate positive listing signals."""
        changes = [
            ListingChange(token="LUNA", exchange="binance", change_type="delisted"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert len(signals) == 0

    def test_listing_signals_from_changes_aggregates_multiple_listings(self) -> None:
        """Token listed on multiple exchanges gets combined signal."""
        changes = [
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
            ListingChange(token="SOL", exchange="coinbase", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        # Should combine into single signal
        assert len(signals) == 1
        assert signals[0].token == "SOL"
        assert signals[0].exchange_count == 2


class TestListingSignalsStrength:
    """ListingSignals assigns strength based on exchange tier."""

    def test_listing_signals_tier1_exchange_high_strength(self) -> None:
        """Tier 1 exchanges (Binance, Coinbase) = high strength."""
        changes = [
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert signals[0].strength >= 0.7

    def test_listing_signals_tier2_exchange_medium_strength(self) -> None:
        """Tier 2 exchanges (Kraken, KuCoin) = medium strength."""
        changes = [
            ListingChange(token="SOL", exchange="kraken", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert 0.3 <= signals[0].strength <= 0.7

    def test_listing_signals_tier3_exchange_low_strength(self) -> None:
        """Tier 3/unknown exchanges = low strength."""
        changes = [
            ListingChange(token="SOL", exchange="small_exchange", change_type="listed"),
        ]
        signals = ListingSignals.from_changes(changes)
        assert signals[0].strength <= 0.3

    def test_listing_signals_multiple_exchanges_boost_strength(self) -> None:
        """Multiple exchange listings should boost overall strength."""
        single = ListingSignals.from_changes([
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
        ])
        multiple = ListingSignals.from_changes([
            ListingChange(token="SOL", exchange="binance", change_type="listed"),
            ListingChange(token="SOL", exchange="coinbase", change_type="listed"),
        ])
        assert multiple[0].strength > single[0].strength


class TestListingSignalsVelocity:
    """ListingSignals.calculate_velocity() measures listing rate."""

    def test_listing_signals_velocity_with_recent_listings(self) -> None:
        """Recent listings produce positive velocity."""
        # Token listed on 3 exchanges in last 7 days
        velocity = ListingSignals.calculate_velocity(total_listings=3, days=7)
        assert velocity > 0

    def test_listing_signals_velocity_zero_when_no_listings(self) -> None:
        velocity = ListingSignals.calculate_velocity(total_listings=0, days=7)
        assert velocity == 0.0

    def test_listing_signals_velocity_higher_for_faster_listings(self) -> None:
        slow = ListingSignals.calculate_velocity(total_listings=1, days=30)
        fast = ListingSignals.calculate_velocity(total_listings=5, days=7)
        assert fast > slow


class TestListingSignalsEmptyInput:
    """ListingSignals handles edge cases."""

    def test_listing_signals_empty_changes_returns_empty_list(self) -> None:
        signals = ListingSignals.from_changes([])
        assert signals == []
