"""Tests for app.graph.centrality_analyzer — TDD Red→Green."""

from __future__ import annotations

import pytest

from app.graph.centrality_analyzer import CentralityAnalyzer, CentralityResult
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


# ---------------------------------------------------------------------------
# TestCentralityResult
# ---------------------------------------------------------------------------


class TestCentralityResult:
    """Unit tests for the CentralityResult dataclass."""

    def test_centrality_result_fields_are_set_correctly(self) -> None:
        """CentralityResult must store symbol, pagerank, betweenness, degree_centrality."""
        cr = CentralityResult(
            symbol="BTC",
            pagerank=0.5,
            betweenness=0.3,
            degree_centrality=0.4,
        )
        assert cr.symbol == "BTC"
        assert cr.pagerank == pytest.approx(0.5)
        assert cr.betweenness == pytest.approx(0.3)
        assert cr.degree_centrality == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# TestCentralityAnalyzerEdgeCases
# ---------------------------------------------------------------------------


class TestCentralityAnalyzerEdgeCases:
    """Edge cases for CentralityAnalyzer."""

    def test_analyze_empty_graph_returns_empty_list(self) -> None:
        """analyze() on an empty graph must return []."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph([])
        assert analyzer.analyze(graph) == []

    def test_analyze_single_node_returns_one_result(self) -> None:
        """analyze() on a single-node graph must return exactly one result."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(["BTC"])
        result = analyzer.analyze(graph)
        assert len(result) == 1
        assert result[0].symbol == "BTC"

    def test_analyze_single_node_centrality_values_are_valid(self) -> None:
        """A single isolated node must have pagerank > 0 and betweenness == 0."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(["BTC"])
        result = analyzer.analyze(graph)
        assert result[0].pagerank > 0
        assert result[0].betweenness == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestCentralityAnalyzerConnected
# ---------------------------------------------------------------------------


class TestCentralityAnalyzerConnected:
    """Tests for CentralityAnalyzer on connected graphs."""

    def test_analyze_returns_result_for_every_node(self) -> None:
        """analyze() must return one CentralityResult per node."""
        analyzer = CentralityAnalyzer()
        symbols = ["BTC", "ETH", "SOL", "AVAX"]
        graph = _build_graph(
            symbols, [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0), ("SOL", "AVAX", 1.0)]
        )
        result = analyzer.analyze(graph)
        assert len(result) == 4
        assert {r.symbol for r in result} == set(symbols)

    def test_analyze_pagerank_values_sum_to_one(self) -> None:
        """PageRank values must sum to approximately 1.0."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(
            ["BTC", "ETH", "SOL"],
            [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0)],
        )
        result = analyzer.analyze(graph)
        total = sum(r.pagerank for r in result)
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_analyze_pagerank_values_are_in_range_zero_to_one(self) -> None:
        """Every pagerank value must be in [0, 1]."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(
            ["BTC", "ETH", "SOL"],
            [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0)],
        )
        result = analyzer.analyze(graph)
        for r in result:
            assert 0.0 <= r.pagerank <= 1.0

    def test_analyze_betweenness_central_node_has_highest_value(self) -> None:
        """In a chain A-B-C, B must have the highest betweenness centrality."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(
            ["A", "B", "C"],
            [("A", "B", 1.0), ("B", "C", 1.0)],
        )
        result = analyzer.analyze(graph)
        by_symbol = {r.symbol: r for r in result}
        assert by_symbol["B"].betweenness >= by_symbol["A"].betweenness
        assert by_symbol["B"].betweenness >= by_symbol["C"].betweenness

    def test_analyze_degree_centrality_hub_has_highest_degree(self) -> None:
        """A hub node (connected to all others) must have the highest degree centrality."""
        analyzer = CentralityAnalyzer()
        # BTC connected to ETH, SOL, AVAX; others only connected to BTC
        graph = _build_graph(
            ["BTC", "ETH", "SOL", "AVAX"],
            [("BTC", "ETH", 1.0), ("BTC", "SOL", 1.0), ("BTC", "AVAX", 1.0)],
        )
        result = analyzer.analyze(graph)
        by_symbol = {r.symbol: r for r in result}
        assert by_symbol["BTC"].degree_centrality > by_symbol["ETH"].degree_centrality


# ---------------------------------------------------------------------------
# TestCentralityAnalyzerTopN
# ---------------------------------------------------------------------------


class TestCentralityAnalyzerTopN:
    """Tests for top_n_by_pagerank()."""

    def test_top_n_by_pagerank_returns_n_results(self) -> None:
        """top_n_by_pagerank(graph, 2) must return exactly 2 results."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(
            ["BTC", "ETH", "SOL"],
            [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0)],
        )
        result = analyzer.top_n_by_pagerank(graph, 2)
        assert len(result) == 2

    def test_top_n_by_pagerank_results_are_sorted_descending(self) -> None:
        """top_n_by_pagerank() must return results in descending pagerank order."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(
            ["BTC", "ETH", "SOL"],
            [("BTC", "ETH", 1.0), ("ETH", "SOL", 1.0)],
        )
        result = analyzer.top_n_by_pagerank(graph, 3)
        for i in range(len(result) - 1):
            assert result[i].pagerank >= result[i + 1].pagerank

    def test_top_n_by_pagerank_n_larger_than_nodes_returns_all(self) -> None:
        """top_n_by_pagerank(graph, 100) must return all nodes when n > node count."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph(["BTC", "ETH"], [("BTC", "ETH", 1.0)])
        result = analyzer.top_n_by_pagerank(graph, 100)
        assert len(result) == 2

    def test_top_n_by_pagerank_empty_graph_returns_empty_list(self) -> None:
        """top_n_by_pagerank() on an empty graph must return []."""
        analyzer = CentralityAnalyzer()
        graph = _build_graph([])
        assert analyzer.top_n_by_pagerank(graph, 5) == []
