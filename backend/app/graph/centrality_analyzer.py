"""Centrality analyser — computes PageRank, betweenness and degree centrality.

This module is part of the Graph Intelligence Layer (Phase 7).
It wraps NetworkX centrality algorithms and surfaces the results as
typed :class:`CentralityResult` objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import networkx as nx
import structlog

if TYPE_CHECKING:
    from app.graph.graph_builder import TokenGraph

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class CentralityResult:
    """Centrality metrics for a single token node.

    Args:
        symbol: Token ticker.
        pagerank: PageRank score (all nodes sum to 1.0).
        betweenness: Betweenness centrality in [0, 1].
        degree_centrality: Degree centrality in [0, 1].
    """

    symbol: str
    pagerank: float
    betweenness: float
    degree_centrality: float


# ---------------------------------------------------------------------------
# CentralityAnalyzer
# ---------------------------------------------------------------------------


class CentralityAnalyzer:
    """Computes centrality metrics for all nodes in a :class:`TokenGraph`.

    Three metrics are computed:

    * **PageRank** — measures global influence via random-walk probability.
    * **Betweenness centrality** — measures how often a node lies on shortest
      paths between other nodes (important bridges).
    * **Degree centrality** — normalised count of direct connections.

    Usage::

        analyzer = CentralityAnalyzer()
        results = analyzer.analyze(token_graph)
        top5 = analyzer.top_n_by_pagerank(token_graph, 5)
    """

    def analyze(self, graph: TokenGraph) -> list[CentralityResult]:
        """Compute centrality metrics for every node in *graph*.

        Args:
            graph: A :class:`TokenGraph` to analyse.

        Returns:
            A list of :class:`CentralityResult` objects, one per node.
            Empty list if the graph has no nodes.
        """
        if graph.node_count() == 0:
            return []

        g: nx.Graph = graph.graph

        pagerank: dict[str, float] = nx.pagerank(g, weight="weight")
        betweenness: dict[str, float] = nx.betweenness_centrality(g, normalized=True)
        degree: dict[str, float] = nx.degree_centrality(g)

        results = [
            CentralityResult(
                symbol=symbol,
                pagerank=pagerank[symbol],
                betweenness=betweenness[symbol],
                degree_centrality=degree[symbol],
            )
            for symbol in g.nodes()
        ]

        logger.info(
            "centrality_analyzer.analyzed",
            n_nodes=len(results),
        )
        return results

    def top_n_by_pagerank(self, graph: TokenGraph, n: int) -> list[CentralityResult]:
        """Return the top *n* nodes sorted by descending PageRank.

        Args:
            graph: A :class:`TokenGraph` to analyse.
            n: Maximum number of results to return.

        Returns:
            Up to *n* :class:`CentralityResult` objects in descending PageRank
            order.  Empty list if the graph has no nodes.
        """
        results = self.analyze(graph)
        results.sort(key=lambda r: r.pagerank, reverse=True)
        return results[:n]
