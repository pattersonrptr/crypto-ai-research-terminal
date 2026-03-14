"""Graph route handlers.

Provides read-only endpoints for the Graph Intelligence Layer (Phase 7):
- GET /graph/communities   — Louvain community detection results
- GET /graph/centrality    — PageRank / betweenness / degree centrality scores
- GET /graph/ecosystem     — Full ecosystem snapshot (communities + top tokens)
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.graph.centrality_analyzer import CentralityAnalyzer
from app.graph.ecosystem_tracker import EcosystemSnapshot, EcosystemTracker
from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph

router = APIRouter()
logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Seed graph — Phase 7 seed data (Phase 8 will replace with live DB read)
# ---------------------------------------------------------------------------

_SEED_NODES: list[NodeAttributes] = [
    NodeAttributes("BTC", 880_000_000_000, "layer1", ecosystem="bitcoin"),
    NodeAttributes("ETH", 350_000_000_000, "layer1", ecosystem="ethereum"),
    NodeAttributes("SOL", 55_000_000_000, "layer1", ecosystem="solana"),
    NodeAttributes("BNB", 85_000_000_000, "layer1", ecosystem="bnb-chain"),
    NodeAttributes("AVAX", 15_000_000_000, "layer1", ecosystem="avalanche"),
    NodeAttributes("ARB", 3_000_000_000, "layer2", narrative="scaling", ecosystem="ethereum"),
    NodeAttributes("OP", 2_500_000_000, "layer2", narrative="scaling", ecosystem="ethereum"),
    NodeAttributes("MATIC", 8_000_000_000, "layer2", narrative="scaling", ecosystem="ethereum"),
    NodeAttributes("LINK", 9_000_000_000, "oracle", ecosystem="ethereum"),
    NodeAttributes("UNI", 6_000_000_000, "defi", ecosystem="ethereum"),
    NodeAttributes("AAVE", 3_500_000_000, "defi", ecosystem="ethereum"),
    NodeAttributes("FET", 1_200_000_000, "defi", narrative="ai", ecosystem="ethereum"),
    NodeAttributes("RNDR", 2_800_000_000, "defi", narrative="ai", ecosystem="ethereum"),
    NodeAttributes("TAO", 2_000_000_000, "layer1", narrative="ai"),
    NodeAttributes("TIA", 4_000_000_000, "layer1", narrative="modular"),
]

_SEED_EDGES: list[EdgeData] = [
    EdgeData("ETH", "ARB", "ecosystem", 0.9),
    EdgeData("ETH", "OP", "ecosystem", 0.9),
    EdgeData("ETH", "MATIC", "ecosystem", 0.85),
    EdgeData("ETH", "LINK", "ecosystem", 0.7),
    EdgeData("ETH", "UNI", "ecosystem", 0.8),
    EdgeData("ETH", "AAVE", "ecosystem", 0.8),
    EdgeData("ETH", "FET", "ecosystem", 0.6),
    EdgeData("ETH", "RNDR", "ecosystem", 0.6),
    EdgeData("ARB", "OP", "correlation", 0.75),
    EdgeData("ARB", "MATIC", "correlation", 0.7),
    EdgeData("UNI", "AAVE", "correlation", 0.65),
    EdgeData("FET", "RNDR", "correlation", 0.8),
    EdgeData("FET", "TAO", "correlation", 0.7),
    EdgeData("RNDR", "TAO", "correlation", 0.65),
    EdgeData("BTC", "ETH", "correlation", 0.8),
    EdgeData("SOL", "AVAX", "correlation", 0.6),
]


def _build_seed_graph() -> TokenGraph:
    """Build and return the static seed TokenGraph."""
    return GraphBuilder().build_from_tokens(_SEED_NODES, _SEED_EDGES)


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------


class CommunityResponse(BaseModel):
    """A detected token community."""

    id: int
    members: list[str]
    size: int


class CentralityResponse(BaseModel):
    """Centrality metrics for a single token."""

    symbol: str
    pagerank: float = Field(ge=0.0)
    betweenness: float = Field(ge=0.0, le=1.0)
    degree_centrality: float = Field(ge=0.0, le=1.0)


class EcosystemResponse(BaseModel):
    """Ecosystem snapshot response."""

    timestamp: str
    n_communities: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    top_tokens: list[str]


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/communities", response_model=list[CommunityResponse])
async def get_communities() -> list[CommunityResponse]:
    """Return detected token communities (Louvain algorithm).

    Each community is a cluster of tokens that are more densely connected
    to each other than to the rest of the graph.
    """
    graph = _build_seed_graph()
    tracker = EcosystemTracker()
    snapshot: EcosystemSnapshot = tracker.snapshot(graph)

    logger.info("graph.get_communities", n_communities=snapshot.n_communities)
    return [
        CommunityResponse(id=c.id, members=c.members, size=c.size) for c in snapshot.communities
    ]


@router.get("/centrality", response_model=list[CentralityResponse])
async def get_centrality(
    top_n: int = Query(default=10, ge=1, description="Maximum results to return"),
) -> list[CentralityResponse]:
    """Return centrality metrics, ranked by PageRank (descending).

    Args:
        top_n: Limit to the top-N tokens by PageRank. Minimum 1.
    """
    graph = _build_seed_graph()
    analyzer = CentralityAnalyzer()
    results = analyzer.top_n_by_pagerank(graph, top_n)

    logger.info("graph.get_centrality", top_n=top_n, returned=len(results))
    return [
        CentralityResponse(
            symbol=r.symbol,
            pagerank=r.pagerank,
            betweenness=r.betweenness,
            degree_centrality=r.degree_centrality,
        )
        for r in results
    ]


@router.get("/ecosystem", response_model=EcosystemResponse)
async def get_ecosystem() -> EcosystemResponse:
    """Return a full ecosystem snapshot.

    Combines community detection and centrality analysis to provide a
    holistic view of the token graph at a point in time.
    """
    graph = _build_seed_graph()
    tracker = EcosystemTracker()
    snapshot: EcosystemSnapshot = tracker.snapshot(graph)

    logger.info(
        "graph.get_ecosystem",
        n_communities=snapshot.n_communities,
        total_tokens=snapshot.total_tokens,
    )
    return EcosystemResponse(
        timestamp=snapshot.timestamp.isoformat(),
        n_communities=snapshot.n_communities,
        total_tokens=snapshot.total_tokens,
        top_tokens=snapshot.top_tokens,
    )
