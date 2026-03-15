"""LiveGraphBuilder — construct a TokenGraph from real token metadata.

Replaces the static seed graph with dynamically-built relationships
derived from shared chains (ecosystem edges) and shared narrative
categories / detected narrative clusters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import structlog

from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Edge weight constants
_ECOSYSTEM_WEIGHT = 0.70
_CATEGORY_WEIGHT = 0.60
_NARRATIVE_WEIGHT = 0.75


@dataclass
class TokenInfo:
    """Lightweight token descriptor used as input for graph construction.

    Attributes:
        symbol: Token ticker, e.g. ``"ETH"``.
        market_cap_usd: Market cap in USD.
        categories: CoinGecko category slugs (e.g. ``["layer1", "smart-contracts"]``).
        chain: Primary blockchain / ecosystem (e.g. ``"ethereum"``).
    """

    symbol: str
    market_cap_usd: float
    categories: list[str] = field(default_factory=list)
    chain: str | None = None


class LiveGraphBuilder:
    """Build a :class:`TokenGraph` from real token metadata and narratives.

    All methods are static — no state is required.
    """

    @staticmethod
    def build(
        tokens: list[TokenInfo],
        *,
        narratives: dict[str, list[str]] | None = None,
    ) -> TokenGraph:
        """Build a :class:`TokenGraph` from token info and optional narratives.

        Args:
            tokens: Token descriptors with market cap, categories, and chain.
            narratives: Optional mapping of narrative name → list of symbols
                        (e.g. from detected :class:`NarrativeCluster` data).

        Returns:
            A fully populated :class:`TokenGraph`.
        """
        if not tokens:
            return TokenGraph()

        nodes = _build_nodes(tokens)
        edges = _build_edges(tokens, narratives or {})

        graph = GraphBuilder().build_from_tokens(nodes, edges)
        logger.info(
            "live_graph_builder.built",
            tokens=len(tokens),
            nodes=graph.node_count(),
            edges=graph.edge_count(),
        )
        return graph


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_nodes(tokens: list[TokenInfo]) -> list[NodeAttributes]:
    """Convert :class:`TokenInfo` list into :class:`NodeAttributes` list."""
    nodes: list[NodeAttributes] = []
    for tok in tokens:
        sector = tok.categories[0] if tok.categories else "unknown"
        narrative = tok.categories[1] if len(tok.categories) > 1 else None
        nodes.append(
            NodeAttributes(
                symbol=tok.symbol,
                market_cap_usd=tok.market_cap_usd,
                sector=sector,
                narrative=narrative,
                ecosystem=tok.chain,
            )
        )
    return nodes


def _build_edges(
    tokens: list[TokenInfo],
    narratives: dict[str, list[str]],
) -> list[EdgeData]:
    """Derive edges from shared chains, shared categories, and narrative clusters."""
    edges: list[EdgeData] = []
    seen: set[tuple[str, str]] = set()

    def _add(src: str, tgt: str, rel: str, weight: float) -> None:
        key = (min(src, tgt), max(src, tgt))
        if key in seen:
            return
        seen.add(key)
        edges.append(EdgeData(source=src, target=tgt, relation_type=rel, weight=weight))

    # 1. Same-chain (ecosystem) edges
    chain_groups: dict[str, list[str]] = {}
    for tok in tokens:
        if tok.chain:
            chain_groups.setdefault(tok.chain, []).append(tok.symbol)

    for _chain, symbols in chain_groups.items():
        for a, b in combinations(symbols, 2):
            _add(a, b, "ecosystem", _ECOSYSTEM_WEIGHT)

    # 2. Shared-category edges
    cat_groups: dict[str, list[str]] = {}
    for tok in tokens:
        for cat in tok.categories:
            cat_groups.setdefault(cat, []).append(tok.symbol)

    for _cat, symbols in cat_groups.items():
        for a, b in combinations(symbols, 2):
            _add(a, b, "category", _CATEGORY_WEIGHT)

    # 3. Narrative cluster edges (from NarrativeDetector output)
    for _name, symbols in narratives.items():
        for a, b in combinations(symbols, 2):
            _add(a, b, "narrative", _NARRATIVE_WEIGHT)

    return edges
