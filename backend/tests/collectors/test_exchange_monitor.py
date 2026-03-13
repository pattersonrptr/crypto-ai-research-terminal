"""Tests for ExchangeMonitor.

Monitors exchange listing changes:
- Track which tokens are listed on which exchanges
- Detect new listings (diff between snapshots)
- Detect delistings
"""

from app.collectors.exchange_monitor import (
    ExchangeMonitor,
    ListingSnapshot,
)


class TestExchangeMonitorSnapshot:
    """ExchangeMonitor.get_snapshot() returns listing state."""

    def test_exchange_monitor_get_snapshot_returns_snapshot(self) -> None:
        # Using mock exchange data
        exchange_data = {
            "binance": ["BTC", "ETH", "SOL"],
            "coinbase": ["BTC", "ETH"],
        }
        snapshot = ExchangeMonitor.get_snapshot(exchange_data)
        assert isinstance(snapshot, ListingSnapshot)

    def test_exchange_monitor_snapshot_contains_all_exchanges(self) -> None:
        exchange_data = {
            "binance": ["BTC", "ETH"],
            "coinbase": ["BTC", "ETH", "AVAX"],
            "kraken": ["BTC"],
        }
        snapshot = ExchangeMonitor.get_snapshot(exchange_data)
        assert "binance" in snapshot.exchange_tokens
        assert "coinbase" in snapshot.exchange_tokens
        assert "kraken" in snapshot.exchange_tokens

    def test_exchange_monitor_snapshot_tracks_token_exchanges(self) -> None:
        exchange_data = {
            "binance": ["BTC", "ETH"],
            "coinbase": ["BTC", "SOL"],
        }
        snapshot = ExchangeMonitor.get_snapshot(exchange_data)
        # BTC is on both
        assert snapshot.token_exchanges["BTC"] == {"binance", "coinbase"}
        # ETH only on binance
        assert snapshot.token_exchanges["ETH"] == {"binance"}
        # SOL only on coinbase
        assert snapshot.token_exchanges["SOL"] == {"coinbase"}


class TestExchangeMonitorDiff:
    """ExchangeMonitor.diff() detects listing changes."""

    def test_exchange_monitor_diff_detects_new_listing(self) -> None:
        old_data = {"binance": ["BTC", "ETH"]}
        new_data = {"binance": ["BTC", "ETH", "SOL"]}  # SOL added

        old_snapshot = ExchangeMonitor.get_snapshot(old_data)
        new_snapshot = ExchangeMonitor.get_snapshot(new_data)

        changes = ExchangeMonitor.diff(old_snapshot, new_snapshot)
        assert len(changes) == 1
        assert changes[0].token == "SOL"
        assert changes[0].exchange == "binance"
        assert changes[0].change_type == "listed"

    def test_exchange_monitor_diff_detects_delisting(self) -> None:
        old_data = {"binance": ["BTC", "ETH", "SOL"]}
        new_data = {"binance": ["BTC", "ETH"]}  # SOL removed

        old_snapshot = ExchangeMonitor.get_snapshot(old_data)
        new_snapshot = ExchangeMonitor.get_snapshot(new_data)

        changes = ExchangeMonitor.diff(old_snapshot, new_snapshot)
        assert len(changes) == 1
        assert changes[0].token == "SOL"
        assert changes[0].exchange == "binance"
        assert changes[0].change_type == "delisted"

    def test_exchange_monitor_diff_returns_empty_when_no_changes(self) -> None:
        data = {"binance": ["BTC", "ETH"], "coinbase": ["BTC", "ETH"]}

        old_snapshot = ExchangeMonitor.get_snapshot(data)
        new_snapshot = ExchangeMonitor.get_snapshot(data)

        changes = ExchangeMonitor.diff(old_snapshot, new_snapshot)
        assert changes == []

    def test_exchange_monitor_diff_handles_new_exchange(self) -> None:
        old_data = {"binance": ["BTC"]}
        new_data = {"binance": ["BTC"], "coinbase": ["BTC", "ETH"]}

        old_snapshot = ExchangeMonitor.get_snapshot(old_data)
        new_snapshot = ExchangeMonitor.get_snapshot(new_data)

        changes = ExchangeMonitor.diff(old_snapshot, new_snapshot)
        # BTC on coinbase is new, ETH on coinbase is new
        listed_tokens = {(c.token, c.exchange) for c in changes if c.change_type == "listed"}
        assert ("BTC", "coinbase") in listed_tokens
        assert ("ETH", "coinbase") in listed_tokens

    def test_exchange_monitor_diff_handles_multiple_changes(self) -> None:
        old_data = {"binance": ["BTC", "ETH", "DOGE"]}
        new_data = {"binance": ["BTC", "SOL", "AVAX"]}  # ETH, DOGE removed; SOL, AVAX added

        old_snapshot = ExchangeMonitor.get_snapshot(old_data)
        new_snapshot = ExchangeMonitor.get_snapshot(new_data)

        changes = ExchangeMonitor.diff(old_snapshot, new_snapshot)

        listed = [c for c in changes if c.change_type == "listed"]
        delisted = [c for c in changes if c.change_type == "delisted"]

        assert len(listed) == 2
        assert len(delisted) == 2
        assert {c.token for c in listed} == {"SOL", "AVAX"}
        assert {c.token for c in delisted} == {"ETH", "DOGE"}


class TestExchangeMonitorTokenExchangeCount:
    """ExchangeMonitor.count_exchanges() returns listing breadth."""

    def test_exchange_monitor_count_exchanges_for_token(self) -> None:
        exchange_data = {
            "binance": ["BTC", "ETH"],
            "coinbase": ["BTC", "ETH"],
            "kraken": ["BTC"],
        }
        snapshot = ExchangeMonitor.get_snapshot(exchange_data)
        assert ExchangeMonitor.count_exchanges(snapshot, "BTC") == 3
        assert ExchangeMonitor.count_exchanges(snapshot, "ETH") == 2
        assert ExchangeMonitor.count_exchanges(snapshot, "DOGE") == 0


class TestExchangeMonitorValidation:
    """ExchangeMonitor validates input data."""

    def test_exchange_monitor_handles_empty_exchange_data(self) -> None:
        snapshot = ExchangeMonitor.get_snapshot({})
        assert snapshot.exchange_tokens == {}
        assert snapshot.token_exchanges == {}

    def test_exchange_monitor_handles_empty_token_list(self) -> None:
        exchange_data = {"binance": [], "coinbase": ["BTC"]}
        snapshot = ExchangeMonitor.get_snapshot(exchange_data)
        assert snapshot.exchange_tokens["binance"] == set()
        assert snapshot.exchange_tokens["coinbase"] == {"BTC"}
