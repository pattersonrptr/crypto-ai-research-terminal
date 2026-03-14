"""Narratives route handlers.

Provides endpoints for viewing detected market narratives:
- GET /narratives - List all active narrative clusters

NOTE: Phase 6 returns curated seed data. Phase 7 will wire the live
NarrativeDetector pipeline that analyses social-media posts.
"""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = structlog.get_logger(__name__)


# ── Pydantic schema ────────────────────────────────────────────────────────


class NarrativeResponse(BaseModel):
    """Narrative cluster response schema."""

    id: int
    name: str
    momentum_score: float = Field(ge=0.0, le=10.0)
    trend: str  # accelerating | stable | declining
    tokens: list[str]
    keywords: list[str]
    token_count: int


# ── Seed data (replaced by live detection in Phase 7) ─────────────────────

_SEED_NARRATIVES: list[NarrativeResponse] = [
    NarrativeResponse(
        id=1,
        name="AI & Machine Learning",
        momentum_score=9.2,
        trend="accelerating",
        tokens=["FET", "RNDR", "TAO", "AGIX", "OCEAN"],
        keywords=["AI agents", "GPU compute", "machine learning", "decentralized AI"],
        token_count=5,
    ),
    NarrativeResponse(
        id=2,
        name="Layer 2 Scaling",
        momentum_score=7.8,
        trend="stable",
        tokens=["ARB", "OP", "MATIC", "STRK", "ZK"],
        keywords=["rollups", "gas fees", "scalability", "Ethereum L2"],
        token_count=5,
    ),
    NarrativeResponse(
        id=3,
        name="Real World Assets (RWA)",
        momentum_score=8.1,
        trend="accelerating",
        tokens=["LINK", "MKR", "ONDO", "CFG", "MPL"],
        keywords=["tokenised assets", "stablecoins", "TradFi", "on-chain bonds"],
        token_count=5,
    ),
    NarrativeResponse(
        id=4,
        name="DeFi Lending & Borrowing",
        momentum_score=6.4,
        trend="stable",
        tokens=["AAVE", "COMP", "CRV", "FRAX"],
        keywords=["yield farming", "liquidity pools", "lending protocols"],
        token_count=4,
    ),
    NarrativeResponse(
        id=5,
        name="Meme & Community Coins",
        momentum_score=5.3,
        trend="declining",
        tokens=["DOGE", "SHIB", "PEPE", "FLOKI", "WIF"],
        keywords=["memecoins", "community driven", "viral", "dog coins"],
        token_count=5,
    ),
]


# ── Endpoint ───────────────────────────────────────────────────────────────


@router.get("/", response_model=list[NarrativeResponse])
async def get_narratives() -> list[NarrativeResponse]:
    """Return the list of active narrative clusters.

    Returns:
        List of NarrativeResponse objects sorted by momentum_score desc.
    """
    logger.info("narratives.list.requested", count=len(_SEED_NARRATIVES))
    return sorted(_SEED_NARRATIVES, key=lambda n: n.momentum_score, reverse=True)
