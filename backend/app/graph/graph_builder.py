"""Graph builder — constructs a TokenGraph from token node/edge data.

This module is part of the Graph Intelligence Layer (Phase 7).
It provides the foundational data structures and the factory that builds
NetworkX graphs from structured token metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class NodeAttributes:
    """Attributes attached to a token node in the graph.

    Args:
        symbol: Unique token ticker (e.g. "BTC").
        market_cap_usd: Market capitalisation in USD.
        sector: Broad sector label (e.g. "layer1", "defi", "nft").
        narrative: Optional narrative tag (e.g. "ai", "rwa").
        ecosystem: Optional parent ecosystem (e.g. "ethereum", "solana").
    """

    symbol: str
    market_cap_usd: float
    sector: str
    narrative: str | None = None
    ecosystem: str | None = None


@dataclass
class EdgeData:
    """Describes a weighted, typed edge between two token nodes.

    Args:
        source: Symbol of the source node.
        target: Symbol of the target node.
        relation_type: Type of relationship (e.g. "correlation", "ecosystem").
        weight: Edge weight in [0, 1]. Defaults to 1.0.
    """

    source: str
    target: str
    relation_type: str
    weight: float = 1.0


# ---------------------------------------------------------------------------
# TokenGraph
# ---------------------------------------------------------------------------


@dataclass
class TokenGraph:
    """Thin wrapper around a :class:`networkx.Graph` for token graphs.

    All nodes are indexed by their token *symbol* (str).
    Node attributes follow the :class:`NodeAttributes` schema.
    Edge attributes include ``weight`` (float) and ``relation_type`` (str).
    """

    graph: nx.Graph = field(default_factory=nx.Graph)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def node_count(self) -> int:
        """Return the total number of nodes in the graph."""
        return int(self.graph.number_of_nodes())

    def edge_count(self) -> int:
        """Return the total number of edges in the graph."""
        return int(self.graph.number_of_edges())

    def has_node(self, symbol: str) -> bool:
        """Return True if *symbol* is present as a node."""
        return bool(self.graph.has_node(symbol))

    def symbols(self) -> list[str]:
        """Return a sorted list of all node symbols in the graph."""
        return sorted(self.graph.nodes())

    def get_node_attributes(self, symbol: str) -> dict[str, Any]:
        """Return the attribute dictionary for the given *symbol* node.

        Returns an empty dict if the node does not exist.
        """
        if not self.graph.has_node(symbol):
            return {}
        return dict(self.graph.nodes[symbol])

    def get_edge_weight(self, source: str, target: str) -> float:
        """Return the weight of the edge between *source* and *target*.

        Returns 0.0 if the edge does not exist.
        """
        if not self.graph.has_edge(source, target):
            return 0.0
        return float(self.graph[source][target].get("weight", 1.0))


# ---------------------------------------------------------------------------
# GraphBuilder
# ---------------------------------------------------------------------------


class GraphBuilder:
    """Factory that constructs :class:`TokenGraph` instances.

    Usage::

        builder = GraphBuilder()
        graph = builder.build_from_tokens(nodes, edges)
    """

    def build_from_tokens(
        self,
        nodes: list[NodeAttributes],
        edges: list[EdgeData],
    ) -> TokenGraph:
        """Build a :class:`TokenGraph` from node and edge descriptors.

        Duplicate nodes (same symbol) are deduplicated — the last entry wins.
        Edges that reference symbols not present in *nodes* are silently skipped
        and a warning is logged.

        Args:
            nodes: Token node descriptors to add to the graph.
            edges: Weighted, typed edge descriptors.

        Returns:
            A fully populated :class:`TokenGraph`.
        """
        g: nx.Graph = nx.Graph()

        # Add nodes (duplicates overwrite; last entry wins)
        for node in nodes:
            attrs: dict[str, Any] = {
                "market_cap_usd": node.market_cap_usd,
                "sector": node.sector,
            }
            if node.narrative is not None:
                attrs["narrative"] = node.narrative
            if node.ecosystem is not None:
                attrs["ecosystem"] = node.ecosystem
            g.add_node(node.symbol, **attrs)

        # Add edges — skip if either endpoint is missing
        known: set[str] = set(g.nodes())
        for edge in edges:
            if edge.source not in known or edge.target not in known:
                logger.warning(
                    "graph_builder.skip_edge",
                    source=edge.source,
                    target=edge.target,
                    reason="node_not_found",
                )
                continue
            g.add_edge(
                edge.source,
                edge.target,
                weight=edge.weight,
                relation_type=edge.relation_type,
            )

        logger.info(
            "graph_builder.built",
            nodes=g.number_of_nodes(),
            edges=g.number_of_edges(),
        )
        return TokenGraph(graph=g)
