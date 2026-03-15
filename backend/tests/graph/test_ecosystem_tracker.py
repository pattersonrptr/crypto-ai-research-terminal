"""Tests for app.graph.ecosystem_tracker — TDD Red→Green."""

from __future__ import annotations

from datetime import UTC, datetime

from app.graph.community_detector import Community
from app.graph.ecosystem_tracker import EcosystemDiff, EcosystemSnapshot, EcosystemTracker
from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_graph(
    symbols: list[str],
    edges: list[tuple[str, str, float]] | None = None,
) -> TokenGraph:
    builder = GraphBuilder()
    nodes = [NodeAttributes(symbol=s, market_cap_usd=1.0, sector="layer1") for s in symbols]
    edge_data = [
        EdgeData(source=src, target=tgt, weight=w, relation_type="correlation")
        for src, tgt, w in (edges or [])
    ]
    return builder.build_from_tokens(nodes, edge_data)


def _make_community(cid: int, members: list[str]) -> Community:
    return Community(id=cid, members=members)


# ---------------------------------------------------------------------------
# TestEcosystemSnapshot
# ---------------------------------------------------------------------------


class TestEcosystemSnapshot:
    """Unit tests for the EcosystemSnapshot dataclass."""

    def test_ecosystem_snapshot_fields_are_set_correctly(self) -> None:
        """EcosystemSnapshot must store timestamp, communities and top_tokens."""
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        communities = [_make_community(0, ["BTC", "ETH"])]
        snap = EcosystemSnapshot(timestamp=ts, communities=communities, top_tokens=["BTC"])
        assert snap.timestamp == ts
        assert len(snap.communities) == 1
        assert snap.top_tokens == ["BTC"]

    def test_ecosystem_snapshot_n_communities_is_len_of_communities(self) -> None:
        """n_communities property must equal len(communities)."""
        snap = EcosystemSnapshot(
            timestamp=datetime.now(tz=UTC),
            communities=[_make_community(0, ["BTC"]), _make_community(1, ["ETH"])],
            top_tokens=[],
        )
        assert snap.n_communities == 2

    def test_ecosystem_snapshot_total_tokens_counts_all_members(self) -> None:
        """total_tokens must equal the sum of sizes across all communities."""
        snap = EcosystemSnapshot(
            timestamp=datetime.now(tz=UTC),
            communities=[
                _make_community(0, ["BTC", "ETH"]),
                _make_community(1, ["SOL"]),
            ],
            top_tokens=[],
        )
        assert snap.total_tokens == 3


# ---------------------------------------------------------------------------
# TestEcosystemDiff
# ---------------------------------------------------------------------------


class TestEcosystemDiff:
    """Unit tests for the EcosystemDiff dataclass."""

    def test_ecosystem_diff_fields_are_set_correctly(self) -> None:
        """EcosystemDiff must expose new_tokens and removed_tokens."""
        diff = EcosystemDiff(new_tokens=["SOL"], removed_tokens=["BNB"])
        assert diff.new_tokens == ["SOL"]
        assert diff.removed_tokens == ["BNB"]

    def test_ecosystem_diff_default_fields_are_empty_lists(self) -> None:
        """EcosystemDiff fields must default to empty lists."""
        diff = EcosystemDiff()
        assert diff.new_tokens == []
        assert diff.removed_tokens == []

    def test_ecosystem_diff_is_empty_returns_true_when_no_changes(self) -> None:
        """is_empty() must return True when there are no new or removed tokens."""
        diff = EcosystemDiff()
        assert diff.is_empty() is True

    def test_ecosystem_diff_is_empty_returns_false_when_has_changes(self) -> None:
        """is_empty() must return False when there are new tokens."""
        diff = EcosystemDiff(new_tokens=["SOL"])
        assert diff.is_empty() is False


# ---------------------------------------------------------------------------
# TestEcosystemTracker
# ---------------------------------------------------------------------------


class TestEcosystemTracker:
    """Tests for EcosystemTracker.snapshot() and compare()."""

    def test_snapshot_returns_ecosystem_snapshot_instance(self) -> None:
        """snapshot() must return an EcosystemSnapshot object."""
        tracker = EcosystemTracker()
        graph = _build_graph(["BTC", "ETH"], [("BTC", "ETH", 1.0)])
        result = tracker.snapshot(graph)
        assert isinstance(result, EcosystemSnapshot)

    def test_snapshot_timestamp_is_utc(self) -> None:
        """snapshot() timestamp must be timezone-aware (UTC)."""
        tracker = EcosystemTracker()
        graph = _build_graph(["BTC"])
        result = tracker.snapshot(graph)
        assert result.timestamp.tzinfo is not None

    def test_snapshot_communities_covers_all_nodes(self) -> None:
        """All graph nodes must appear in some community of the snapshot."""
        tracker = EcosystemTracker()
        symbols = ["BTC", "ETH", "SOL"]
        graph = _build_graph(symbols, [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0)])
        result = tracker.snapshot(graph)
        all_members = {m for c in result.communities for m in c.members}
        assert all_members == set(symbols)

    def test_snapshot_top_tokens_is_non_empty_for_non_empty_graph(self) -> None:
        """snapshot().top_tokens must be non-empty for a non-empty graph."""
        tracker = EcosystemTracker()
        graph = _build_graph(["BTC", "ETH"], [("BTC", "ETH", 1.0)])
        result = tracker.snapshot(graph)
        assert len(result.top_tokens) > 0

    def test_snapshot_top_tokens_are_valid_symbols(self) -> None:
        """Every symbol in top_tokens must be a node in the graph."""
        tracker = EcosystemTracker()
        graph = _build_graph(["BTC", "ETH", "SOL"], [("BTC", "ETH", 1.0)])
        result = tracker.snapshot(graph)
        for symbol in result.top_tokens:
            assert graph.has_node(symbol)

    def test_snapshot_empty_graph_returns_empty_snapshot(self) -> None:
        """snapshot() on an empty graph must have 0 communities and 0 top_tokens."""
        tracker = EcosystemTracker()
        graph = _build_graph([])
        result = tracker.snapshot(graph)
        assert result.n_communities == 0
        assert result.top_tokens == []

    def test_compare_identical_snapshots_returns_empty_diff(self) -> None:
        """compare() on two identical snapshots must return an empty EcosystemDiff."""
        tracker = EcosystemTracker()
        graph = _build_graph(["BTC", "ETH"], [("BTC", "ETH", 1.0)])
        snap = tracker.snapshot(graph)
        diff = tracker.compare(snap, snap)
        assert diff.is_empty()

    def test_compare_detects_new_tokens(self) -> None:
        """compare() must list tokens that appear in snap2 but not snap1."""
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        diff = tracker.compare(snap1, snap2)
        assert "ETH" in diff.new_tokens
        assert diff.removed_tokens == []

    def test_compare_detects_removed_tokens(self) -> None:
        """compare() must list tokens that were in snap1 but absent from snap2."""
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC"])],
            top_tokens=["BTC"],
        )
        diff = tracker.compare(snap1, snap2)
        assert "ETH" in diff.removed_tokens
        assert diff.new_tokens == []

    def test_compare_detects_both_new_and_removed_tokens(self) -> None:
        """compare() must correctly report both new and removed tokens simultaneously."""
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "SOL"])],
            top_tokens=["BTC"],
        )
        diff = tracker.compare(snap1, snap2)
        assert "SOL" in diff.new_tokens
        assert "ETH" in diff.removed_tokens


# ---------------------------------------------------------------------------
# TestEcosystemTracker.growth_summary
# ---------------------------------------------------------------------------


class TestEcosystemTrackerGrowthSummary:
    """growth_summary() compares community sizes over time."""

    def test_growth_summary_reports_total_delta(self) -> None:
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH", "SOL", "AVAX"])],
            top_tokens=["BTC"],
        )
        summary = tracker.growth_summary(snap1, snap2)
        assert summary["total_tokens_before"] == 2
        assert summary["total_tokens_after"] == 4
        assert summary["net_growth"] == 2

    def test_growth_summary_reports_community_count_delta(self) -> None:
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[
                _make_community(0, ["BTC", "ETH"]),
                _make_community(1, ["SOL", "AVAX"]),
            ],
            top_tokens=["BTC"],
        )
        summary = tracker.growth_summary(snap1, snap2)
        assert summary["communities_before"] == 1
        assert summary["communities_after"] == 2

    def test_growth_summary_label_growing(self) -> None:
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH", "SOL"])],
            top_tokens=["BTC"],
        )
        summary = tracker.growth_summary(snap1, snap2)
        assert summary["trend"] == "growing"

    def test_growth_summary_label_shrinking(self) -> None:
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap1 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH", "SOL"])],
            top_tokens=["BTC"],
        )
        snap2 = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC"])],
            top_tokens=["BTC"],
        )
        summary = tracker.growth_summary(snap1, snap2)
        assert summary["trend"] == "shrinking"

    def test_growth_summary_label_stable(self) -> None:
        tracker = EcosystemTracker()
        ts = datetime(2024, 1, 1, tzinfo=UTC)
        snap = EcosystemSnapshot(
            timestamp=ts,
            communities=[_make_community(0, ["BTC", "ETH"])],
            top_tokens=["BTC"],
        )
        summary = tracker.growth_summary(snap, snap)
        assert summary["trend"] == "stable"
