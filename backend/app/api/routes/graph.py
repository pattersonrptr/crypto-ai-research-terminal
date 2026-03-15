"""Graph route handlers.

Provides read-only endpoints for the Graph Intelligence Layer (Phase 7):
- GET /graph/communities   — Louvain community detection results
- GET /graph/centrality    — PageRank / betweenness / degree centrality scores
- GET /graph/ecosystem     — Full ecosystem snapshot (communities + top tokens)

Phase 10: supports live graph construction via :class:`LiveGraphBuilder` when
token data is available, falling back to static seed data.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.graph.centrality_analyzer import CentralityAnalyzer
from app.graph.ecosystem_tracker import EcosystemSnapshot, EcosystemTracker
from app.graph.graph_builder import EdgeData, GraphBuilder, NodeAttributes, TokenGraph
from app.graph.live_graph_builder import LiveGraphBuilder, TokenInfo

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


async def _build_live_graph() -> TokenGraph | None:
    """Attempt to build a live graph from DB token data.

    Returns ``None`` when the DB is unreachable or has no tokens, in which
    case callers should fall back to :func:`_build_seed_graph`.
    """
    try:
        from sqlalchemy import text  # noqa: PLC0415
        from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415

        from app.config import settings  # noqa: PLC0415

        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT t.symbol, md.market_cap_usd "
                    "FROM tokens t "
                    "JOIN market_data md ON md.token_id = t.id "
                    "ORDER BY md.collected_at DESC "
                    "LIMIT 250"
                )
            )
            rows = result.fetchall()

        if not rows:
            return None

        tokens: list[TokenInfo] = []
        for row in rows:
            tokens.append(
                TokenInfo(
                    symbol=row.symbol,
                    market_cap_usd=float(row.market_cap_usd or 0),
                )
            )

        graph = LiveGraphBuilder.build(tokens)
        logger.info("graph.live_build", nodes=graph.node_count(), edges=graph.edge_count())
        return graph
    except Exception:
        logger.warning("graph.live_build_failed")
        return None


async def _get_graph() -> TokenGraph:
    """Return a live graph if available, otherwise the seed graph."""
    live = await _build_live_graph()
    if live is not None and live.node_count() > 0:
        return live
    return _build_seed_graph()


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
    graph = await _get_graph()
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
    graph = await _get_graph()
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
    graph = await _get_graph()
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
