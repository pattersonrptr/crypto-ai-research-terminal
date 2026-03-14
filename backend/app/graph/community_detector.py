"""Community detector — applies the Louvain algorithm to a TokenGraph.

Uses the ``python-louvain`` package (import name: ``community``) which
implements the Louvain method for community detection on undirected graphs.
The result is a list of :class:`Community` objects, one per detected cluster.

This module is part of the Graph Intelligence Layer (Phase 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import community as community_louvain  # nosec
import structlog

if TYPE_CHECKING:
    from app.graph.graph_builder import TokenGraph

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class Community:
    """A community (cluster) of token symbols detected in the graph.

    Args:
        id: Non-negative integer identifier for this community.
        members: Token symbols that belong to this community.
                 Stored in sorted order; ``size`` is derived automatically.
    """

    id: int
    members: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.members = sorted(self.members)

    @property
    def size(self) -> int:
        """Return the number of tokens in this community."""
        return len(self.members)


# ---------------------------------------------------------------------------
# CommunityDetector
# ---------------------------------------------------------------------------


class CommunityDetector:
    """Detects communities in a :class:`TokenGraph` using the Louvain algorithm.

    The Louvain method maximises modularity and produces a partition where every
    node belongs to exactly one community (hard partition).

    Usage::

        detector = CommunityDetector()
        communities = detector.detect(token_graph)
    """

    def detect(self, graph: TokenGraph) -> list[Community]:
        """Detect communities in *graph* using the Louvain method.

        Args:
            graph: A :class:`TokenGraph` to partition.

        Returns:
            A list of :class:`Community` objects.  Empty list if the graph has
            no nodes.  The list is sorted by community id (ascending).
        """
        if graph.node_count() == 0:
            return []

        partition: dict[str, int] = community_louvain.best_partition(graph.graph)

        # Group symbols by community id
        groups: dict[int, list[str]] = {}
        for symbol, cid in partition.items():
            groups.setdefault(cid, []).append(symbol)

        communities = [Community(id=cid, members=members) for cid, members in groups.items()]
        communities.sort(key=lambda c: c.id)

        logger.info(
            "community_detector.detected",
            n_communities=len(communities),
            n_nodes=graph.node_count(),
        )
        return communities
