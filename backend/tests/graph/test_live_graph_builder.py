"""Tests for LiveGraphBuilder — build graph from real token + narrative data.

TDD RED phase: tests that verify the LiveGraphBuilder creates a TokenGraph
from token metadata and detected narratives.
"""

from __future__ import annotations

from app.graph.graph_builder import TokenGraph
from app.graph.live_graph_builder import LiveGraphBuilder, TokenInfo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tok(
    symbol: str,
    market_cap: float = 1_000_000_000,
    *,
    categories: list[str] | None = None,
    chain: str | None = None,
) -> TokenInfo:
    """Shorthand for creating a TokenInfo."""
    return TokenInfo(
        symbol=symbol,
        market_cap_usd=market_cap,
        categories=categories or [],
        chain=chain,
    )


# ---------------------------------------------------------------------------
# TokenInfo
# ---------------------------------------------------------------------------


class TestTokenInfo:
    """TokenInfo carries the data needed to build graph nodes."""

    def test_create_token_info(self) -> None:
        info = _tok("BTC", 800e9, categories=["layer1"], chain="bitcoin")
        assert info.symbol == "BTC"
        assert info.market_cap_usd == 800e9
        assert info.categories == ["layer1"]
        assert info.chain == "bitcoin"

    def test_defaults(self) -> None:
        info = TokenInfo(symbol="X", market_cap_usd=100)
        assert info.categories == []
        assert info.chain is None


# ---------------------------------------------------------------------------
# LiveGraphBuilder.build
# ---------------------------------------------------------------------------


class TestLiveGraphBuilderBuild:
    """LiveGraphBuilder.build() creates a TokenGraph from token metadata."""

    def test_build_returns_token_graph(self) -> None:
        tokens = [_tok("BTC"), _tok("ETH")]
        graph = LiveGraphBuilder.build(tokens)
        assert isinstance(graph, TokenGraph)

    def test_nodes_from_tokens(self) -> None:
        tokens = [_tok("BTC", 800e9), _tok("ETH", 350e9)]
        graph = LiveGraphBuilder.build(tokens)
        assert graph.node_count() == 2
        assert graph.has_node("BTC")
        assert graph.has_node("ETH")

    def test_node_attributes_populated(self) -> None:
        tokens = [_tok("FET", 1.2e9, categories=["defi", "ai"], chain="ethereum")]
        graph = LiveGraphBuilder.build(tokens)
        attrs = graph.get_node_attributes("FET")
        assert attrs["market_cap_usd"] == 1.2e9
        assert attrs["ecosystem"] == "ethereum"

    def test_same_chain_creates_ecosystem_edge(self) -> None:
        """Tokens on the same chain should be connected via ecosystem edge."""
        tokens = [
            _tok("AAVE", 3.5e9, categories=["defi"], chain="ethereum"),
            _tok("UNI", 6e9, categories=["defi"], chain="ethereum"),
        ]
        graph = LiveGraphBuilder.build(tokens)
        assert graph.edge_count() >= 1
        assert graph.get_edge_weight("AAVE", "UNI") > 0

    def test_shared_category_creates_narrative_edge(self) -> None:
        """Tokens sharing a category should get a narrative edge."""
        tokens = [
            _tok("FET", 1.2e9, categories=["ai"]),
            _tok("RNDR", 2.8e9, categories=["ai"]),
        ]
        graph = LiveGraphBuilder.build(tokens)
        assert graph.get_edge_weight("FET", "RNDR") > 0

    def test_no_edge_between_unrelated_tokens(self) -> None:
        """Tokens with different chains and no shared categories stay unlinked."""
        tokens = [
            _tok("BTC", 800e9, categories=["layer1"], chain="bitcoin"),
            _tok("DOGE", 10e9, categories=["meme"], chain="dogecoin"),
        ]
        graph = LiveGraphBuilder.build(tokens)
        assert graph.get_edge_weight("BTC", "DOGE") == 0.0

    def test_empty_input_returns_empty_graph(self) -> None:
        graph = LiveGraphBuilder.build([])
        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_single_token_no_edges(self) -> None:
        graph = LiveGraphBuilder.build([_tok("BTC")])
        assert graph.node_count() == 1
        assert graph.edge_count() == 0

    def test_sector_from_first_category(self) -> None:
        """The first category becomes the node's sector attribute."""
        tokens = [_tok("SOL", 55e9, categories=["layer1", "smart-contracts"])]
        graph = LiveGraphBuilder.build(tokens)
        attrs = graph.get_node_attributes("SOL")
        assert attrs["sector"] == "layer1"

    def test_narrative_from_second_category(self) -> None:
        """If multiple categories, the second becomes the narrative."""
        tokens = [_tok("FET", 1.2e9, categories=["defi", "ai"])]
        graph = LiveGraphBuilder.build(tokens)
        attrs = graph.get_node_attributes("FET")
        assert attrs.get("narrative") == "ai"

    def test_with_narrative_clusters(self) -> None:
        """Tokens co-occurring in a narrative cluster get a narrative edge."""
        tokens = [
            _tok("FET", 1.2e9),
            _tok("RNDR", 2.8e9),
            _tok("TAO", 2.0e9),
        ]
        narratives = {"ai": ["FET", "RNDR", "TAO"]}
        graph = LiveGraphBuilder.build(tokens, narratives=narratives)
        # All three should have pairwise narrative edges
        assert graph.get_edge_weight("FET", "RNDR") > 0
        assert graph.get_edge_weight("FET", "TAO") > 0
        assert graph.get_edge_weight("RNDR", "TAO") > 0
