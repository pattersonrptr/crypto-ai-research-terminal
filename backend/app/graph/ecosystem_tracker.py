"""Ecosystem tracker — snapshots and diffs of the token ecosystem over time.

Combines community detection and centrality analysis to produce a timed
:class:`EcosystemSnapshot`, and can compare two snapshots to surface
tokens that entered or left the ecosystem.

This module is part of the Graph Intelligence Layer (Phase 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from app.graph.centrality_analyzer import CentralityAnalyzer
from app.graph.community_detector import Community, CommunityDetector

if TYPE_CHECKING:
    from app.graph.graph_builder import TokenGraph

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_TOP_N_DEFAULT: int = 10

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EcosystemSnapshot:
    """A point-in-time snapshot of the token ecosystem.

    Args:
        timestamp: UTC datetime when the snapshot was taken.
        communities: List of detected communities at this point in time.
        top_tokens: Symbols of the top tokens ranked by PageRank.
    """

    timestamp: datetime
    communities: list[Community]
    top_tokens: list[str]

    @property
    def n_communities(self) -> int:
        """Return the number of communities in this snapshot."""
        return len(self.communities)

    @property
    def total_tokens(self) -> int:
        """Return the total number of tokens across all communities."""
        return sum(c.size for c in self.communities)


@dataclass
class EcosystemDiff:
    """Difference between two :class:`EcosystemSnapshot` instances.

    Args:
        new_tokens: Tokens present in the *newer* snapshot but not the older.
        removed_tokens: Tokens present in the *older* snapshot but not the newer.
    """

    new_tokens: list[str] = field(default_factory=list)
    removed_tokens: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Return True when there are no new or removed tokens."""
        return not self.new_tokens and not self.removed_tokens


# ---------------------------------------------------------------------------
# EcosystemTracker
# ---------------------------------------------------------------------------


class EcosystemTracker:
    """Tracks ecosystem evolution by snapshotting and comparing :class:`TokenGraph` states.

    Usage::

        tracker = EcosystemTracker()
        snap1 = tracker.snapshot(graph_t1)
        snap2 = tracker.snapshot(graph_t2)
        diff  = tracker.compare(snap1, snap2)
    """

    def __init__(self, top_n: int = _TOP_N_DEFAULT) -> None:
        """Initialise the tracker.

        Args:
            top_n: Number of top tokens (by PageRank) to include in each
                   snapshot.  Defaults to 10.
        """
        self._top_n = top_n
        self._detector = CommunityDetector()
        self._analyzer = CentralityAnalyzer()

    def snapshot(self, graph: TokenGraph) -> EcosystemSnapshot:
        """Create an :class:`EcosystemSnapshot` from the current graph state.

        Args:
            graph: The :class:`TokenGraph` to snapshot.

        Returns:
            A fully populated :class:`EcosystemSnapshot` with a UTC timestamp.
        """
        now = datetime.now(tz=UTC)
        communities = self._detector.detect(graph)
        top_results = self._analyzer.top_n_by_pagerank(graph, self._top_n)
        top_tokens = [r.symbol for r in top_results]

        snap = EcosystemSnapshot(
            timestamp=now,
            communities=communities,
            top_tokens=top_tokens,
        )
        logger.info(
            "ecosystem_tracker.snapshot",
            n_communities=snap.n_communities,
            total_tokens=snap.total_tokens,
            top_n=len(top_tokens),
        )
        return snap

    def compare(self, snap1: EcosystemSnapshot, snap2: EcosystemSnapshot) -> EcosystemDiff:
        """Compare two snapshots and return the token-level difference.

        Tokens that appear in *snap2* but not *snap1* are *new*.
        Tokens that appear in *snap1* but not *snap2* are *removed*.

        Args:
            snap1: The earlier (reference) snapshot.
            snap2: The later snapshot to compare against.

        Returns:
            An :class:`EcosystemDiff` with sorted ``new_tokens`` and
            ``removed_tokens`` lists.
        """
        tokens1: set[str] = {m for c in snap1.communities for m in c.members}
        tokens2: set[str] = {m for c in snap2.communities for m in c.members}

        new_tokens = sorted(tokens2 - tokens1)
        removed_tokens = sorted(tokens1 - tokens2)

        diff = EcosystemDiff(new_tokens=new_tokens, removed_tokens=removed_tokens)
        logger.info(
            "ecosystem_tracker.compared",
            new=len(new_tokens),
            removed=len(removed_tokens),
        )
        return diff
