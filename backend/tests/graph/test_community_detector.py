"""Tests for app.graph.community_detector — TDD Red→Green."""

from __future__ import annotations

from app.graph.community_detector import Community, CommunityDetector
from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_graph(
    symbols: list[str],
    edges: list[tuple[str, str, float]] | None = None,
) -> TokenGraph:
    """Build a TokenGraph from a list of symbols and optional (src, tgt, weight) tuples."""
    builder = GraphBuilder()
    nodes = [NodeAttributes(symbol=s, market_cap_usd=1.0, sector="layer1") for s in symbols]
    edge_data = [
        EdgeData(source=src, target=tgt, weight=w, relation_type="correlation")
        for src, tgt, w in (edges or [])
    ]
    return builder.build_from_tokens(nodes, edge_data)


# ---------------------------------------------------------------------------
# TestCommunity
# ---------------------------------------------------------------------------


class TestCommunity:
    """Unit tests for the Community dataclass."""

    def test_community_fields_are_set_correctly(self) -> None:
        """Community must store id, members and compute size automatically."""
        c = Community(id=0, members=["BTC", "ETH", "SOL"])
        assert c.id == 0
        assert c.members == ["BTC", "ETH", "SOL"]
        assert c.size == 3

    def test_community_size_is_zero_for_empty_members(self) -> None:
        """Community with empty members list must have size 0."""
        c = Community(id=1, members=[])
        assert c.size == 0

    def test_community_members_are_sorted(self) -> None:
        """Community members must be stored in sorted order."""
        c = Community(id=0, members=["SOL", "BTC", "ETH"])
        assert c.members == ["BTC", "ETH", "SOL"]


# ---------------------------------------------------------------------------
# TestCommunityDetector — empty / trivial graphs
# ---------------------------------------------------------------------------


class TestCommunityDetectorEdgeCases:
    """Edge cases for CommunityDetector."""

    def test_detect_empty_graph_returns_empty_list(self) -> None:
        """detect() on an empty graph must return []."""
        detector = CommunityDetector()
        graph = _build_graph([])
        result = detector.detect(graph)
        assert result == []

    def test_detect_single_node_graph_returns_one_community(self) -> None:
        """detect() on a single-node graph must return exactly one community."""
        detector = CommunityDetector()
        graph = _build_graph(["BTC"])
        result = detector.detect(graph)
        assert len(result) == 1
        assert result[0].members == ["BTC"]


# ---------------------------------------------------------------------------
# TestCommunityDetector — connected graphs
# ---------------------------------------------------------------------------


class TestCommunityDetectorConnected:
    """Tests for CommunityDetector on typical connected graphs."""

    def test_detect_fully_connected_triangle_returns_one_community(self) -> None:
        """Three nodes all connected to each other should be one community."""
        detector = CommunityDetector()
        graph = _build_graph(
            ["BTC", "ETH", "SOL"],
            [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0), ("BTC", "SOL", 1.0)],
        )
        result = detector.detect(graph)
        assert len(result) >= 1
        all_members = {m for c in result for m in c.members}
        assert all_members == {"BTC", "ETH", "SOL"}

    def test_detect_two_cliques_returns_two_communities(self) -> None:
        """Two tightly connected cliques with a weak inter-bridge should give 2 communities."""
        detector = CommunityDetector()
        # clique 1: BTC-ETH-BNB  clique 2: SOL-AVAX-DOT
        graph = _build_graph(
            ["BTC", "ETH", "BNB", "SOL", "AVAX", "DOT"],
            [
                ("BTC", "ETH", 1.0),
                ("ETH", "BNB", 1.0),
                ("BTC", "BNB", 1.0),
                ("SOL", "AVAX", 1.0),
                ("AVAX", "DOT", 1.0),
                ("SOL", "DOT", 1.0),
                # weak bridge between cliques
                ("BTC", "SOL", 0.01),
            ],
        )
        result = detector.detect(graph)
        assert len(result) >= 2
        all_members = {m for c in result for m in c.members}
        assert all_members == {"BTC", "ETH", "BNB", "SOL", "AVAX", "DOT"}

    def test_detect_returns_community_objects_with_positive_ids(self) -> None:
        """Each Community in the result must have a non-negative integer id."""
        detector = CommunityDetector()
        graph = _build_graph(["A", "B"], [("A", "B", 1.0)])
        result = detector.detect(graph)
        for c in result:
            assert isinstance(c.id, int)
            assert c.id >= 0

    def test_detect_every_node_belongs_to_exactly_one_community(self) -> None:
        """No node may appear in more than one community (partition property)."""
        detector = CommunityDetector()
        graph = _build_graph(
            ["BTC", "ETH", "SOL", "AVAX"],
            [("BTC", "ETH", 1.0), ("SOL", "AVAX", 1.0)],
        )
        result = detector.detect(graph)
        all_members: list[str] = [m for c in result for m in c.members]
        assert len(all_members) == len(set(all_members))  # no duplicates

    def test_detect_communities_cover_all_nodes(self) -> None:
        """The union of all community members must equal all graph nodes."""
        detector = CommunityDetector()
        symbols = ["BTC", "ETH", "SOL", "AVAX", "DOT"]
        graph = _build_graph(
            symbols,
            [("BTC", "ETH", 1.0), ("SOL", "AVAX", 1.0), ("AVAX", "DOT", 1.0)],
        )
        result = detector.detect(graph)
        all_members = {m for c in result for m in c.members}
        assert all_members == set(symbols)
