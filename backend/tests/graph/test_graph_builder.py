"""Tests for app.graph.graph_builder — TDD Red→Green."""

from __future__ import annotations

import pytest

from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def builder() -> GraphBuilder:
    """Return a fresh GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture()
def simple_graph(builder: GraphBuilder) -> TokenGraph:
    """Return a TokenGraph with 3 nodes and 2 edges."""
    nodes: list[NodeAttributes] = [
        NodeAttributes(symbol="BTC", market_cap_usd=1_000_000.0, sector="layer1"),
        NodeAttributes(symbol="ETH", market_cap_usd=500_000.0, sector="layer1"),
        NodeAttributes(symbol="SOL", market_cap_usd=100_000.0, sector="layer1"),
    ]
    edges: list[EdgeData] = [
        EdgeData(source="BTC", target="ETH", weight=0.9, relation_type="correlation"),
        EdgeData(source="ETH", target="SOL", weight=0.7, relation_type="ecosystem"),
    ]
    return builder.build_from_tokens(nodes, edges)


# ---------------------------------------------------------------------------
# TestNodeAttributes
# ---------------------------------------------------------------------------


class TestNodeAttributes:
    """Unit tests for the NodeAttributes dataclass."""

    def test_node_attributes_required_fields_are_set(self) -> None:
        """NodeAttributes must store symbol, market_cap_usd and sector."""
        node = NodeAttributes(symbol="BTC", market_cap_usd=1_000_000.0, sector="layer1")
        assert node.symbol == "BTC"
        assert node.market_cap_usd == 1_000_000.0
        assert node.sector == "layer1"

    def test_node_attributes_optional_fields_default_to_none(self) -> None:
        """NodeAttributes optional fields must default to None."""
        node = NodeAttributes(symbol="BTC", market_cap_usd=1_000_000.0, sector="layer1")
        assert node.narrative is None
        assert node.ecosystem is None


# ---------------------------------------------------------------------------
# TestEdgeData
# ---------------------------------------------------------------------------


class TestEdgeData:
    """Unit tests for the EdgeData dataclass."""

    def test_edge_data_fields_are_set_correctly(self) -> None:
        """EdgeData must store source, target, weight and relation_type."""
        edge = EdgeData(source="BTC", target="ETH", weight=0.9, relation_type="correlation")
        assert edge.source == "BTC"
        assert edge.target == "ETH"
        assert edge.weight == 0.9
        assert edge.relation_type == "correlation"

    def test_edge_data_weight_default_is_one(self) -> None:
        """EdgeData weight must default to 1.0 when omitted."""
        edge = EdgeData(source="A", target="B", relation_type="ecosystem")
        assert edge.weight == 1.0


# ---------------------------------------------------------------------------
# TestTokenGraph
# ---------------------------------------------------------------------------


class TestTokenGraph:
    """Unit tests for the TokenGraph wrapper."""

    def test_token_graph_node_count_returns_correct_value(self, simple_graph: TokenGraph) -> None:
        """node_count() must return the number of nodes in the graph."""
        assert simple_graph.node_count() == 3

    def test_token_graph_edge_count_returns_correct_value(self, simple_graph: TokenGraph) -> None:
        """edge_count() must return the number of edges in the graph."""
        assert simple_graph.edge_count() == 2

    def test_token_graph_has_node_returns_true_for_existing_node(
        self, simple_graph: TokenGraph
    ) -> None:
        """has_node() must return True when the symbol exists in the graph."""
        assert simple_graph.has_node("BTC") is True

    def test_token_graph_has_node_returns_false_for_missing_node(
        self, simple_graph: TokenGraph
    ) -> None:
        """has_node() must return False when the symbol is not in the graph."""
        assert simple_graph.has_node("DOGE") is False

    def test_token_graph_empty_graph_has_zero_nodes(self) -> None:
        """A default TokenGraph must have 0 nodes and 0 edges."""
        graph = TokenGraph()
        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_token_graph_node_attributes_are_stored(self, simple_graph: TokenGraph) -> None:
        """Node attributes (market_cap_usd, sector) must be stored in the graph."""
        attrs = simple_graph.get_node_attributes("BTC")
        assert attrs["market_cap_usd"] == 1_000_000.0
        assert attrs["sector"] == "layer1"

    def test_token_graph_edge_weight_is_stored(self, simple_graph: TokenGraph) -> None:
        """Edge weight must be stored as a graph attribute."""
        weight = simple_graph.get_edge_weight("BTC", "ETH")
        assert weight == pytest.approx(0.9)

    def test_token_graph_get_edge_weight_missing_edge_returns_zero(
        self, simple_graph: TokenGraph
    ) -> None:
        """get_edge_weight() on a non-existent edge must return 0.0."""
        assert simple_graph.get_edge_weight("BTC", "SOL") == pytest.approx(0.0)

    def test_token_graph_symbols_returns_all_node_symbols(self, simple_graph: TokenGraph) -> None:
        """symbols() must return a sorted list of all node symbols."""
        assert simple_graph.symbols() == ["BTC", "ETH", "SOL"]

    def test_token_graph_networkx_graph_is_accessible(self, simple_graph: TokenGraph) -> None:
        """The underlying NetworkX graph must be accessible via .graph attribute."""
        import networkx as nx

        assert isinstance(simple_graph.graph, nx.Graph)


# ---------------------------------------------------------------------------
# TestGraphBuilder
# ---------------------------------------------------------------------------


class TestGraphBuilder:
    """Unit tests for the GraphBuilder factory."""

    def test_build_from_tokens_empty_input_returns_empty_graph(self, builder: GraphBuilder) -> None:
        """build_from_tokens([], []) must return a TokenGraph with 0 nodes."""
        result = builder.build_from_tokens([], [])
        assert result.node_count() == 0
        assert result.edge_count() == 0

    def test_build_from_tokens_nodes_only_returns_graph_with_no_edges(
        self, builder: GraphBuilder
    ) -> None:
        """build_from_tokens with nodes but no edges must return 0 edges."""
        nodes = [NodeAttributes(symbol="BTC", market_cap_usd=1.0, sector="layer1")]
        result = builder.build_from_tokens(nodes, [])
        assert result.node_count() == 1
        assert result.edge_count() == 0

    def test_build_from_tokens_creates_nodes_for_each_token(self, builder: GraphBuilder) -> None:
        """build_from_tokens must create one node per NodeAttributes item."""
        nodes = [
            NodeAttributes(symbol="BTC", market_cap_usd=1.0, sector="layer1"),
            NodeAttributes(symbol="ETH", market_cap_usd=1.0, sector="layer1"),
        ]
        result = builder.build_from_tokens(nodes, [])
        assert result.node_count() == 2
        assert result.has_node("BTC")
        assert result.has_node("ETH")

    def test_build_from_tokens_creates_edges_between_tokens(self, builder: GraphBuilder) -> None:
        """build_from_tokens must create one edge per EdgeData item."""
        nodes = [
            NodeAttributes(symbol="BTC", market_cap_usd=1.0, sector="layer1"),
            NodeAttributes(symbol="ETH", market_cap_usd=1.0, sector="layer1"),
        ]
        edges = [EdgeData(source="BTC", target="ETH", weight=0.8, relation_type="correlation")]
        result = builder.build_from_tokens(nodes, edges)
        assert result.edge_count() == 1
        assert result.get_edge_weight("BTC", "ETH") == pytest.approx(0.8)

    def test_build_from_tokens_duplicate_nodes_are_deduplicated(
        self, builder: GraphBuilder
    ) -> None:
        """Duplicate symbols in nodes list must result in a single node."""
        nodes = [
            NodeAttributes(symbol="BTC", market_cap_usd=1.0, sector="layer1"),
            NodeAttributes(symbol="BTC", market_cap_usd=2.0, sector="layer1"),
        ]
        result = builder.build_from_tokens(nodes, [])
        assert result.node_count() == 1

    def test_build_from_tokens_edge_with_unknown_node_is_skipped(
        self, builder: GraphBuilder
    ) -> None:
        """Edges referencing nodes not in the node list must be skipped."""
        nodes = [NodeAttributes(symbol="BTC", market_cap_usd=1.0, sector="layer1")]
        edges = [EdgeData(source="BTC", target="GHOST", weight=0.5, relation_type="correlation")]
        result = builder.build_from_tokens(nodes, edges)
        assert result.edge_count() == 0

    def test_build_from_tokens_optional_node_fields_stored(self, builder: GraphBuilder) -> None:
        """Optional node fields (narrative, ecosystem) must be stored when provided."""
        nodes = [
            NodeAttributes(
                symbol="ETH",
                market_cap_usd=500.0,
                sector="layer1",
                narrative="defi",
                ecosystem="ethereum",
            )
        ]
        result = builder.build_from_tokens(nodes, [])
        attrs = result.get_node_attributes("ETH")
        assert attrs["narrative"] == "defi"
        assert attrs["ecosystem"] == "ethereum"
