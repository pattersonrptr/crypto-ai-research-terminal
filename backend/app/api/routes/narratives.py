"""Narratives route handlers.

Provides endpoints for viewing detected market narratives:
- GET /narratives - List all active narrative clusters

Phase 8: tries to load live narratives from DB/NarrativeDetector first;
falls back to curated seed data when none are available.
"""

from typing import Any

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


# ── Seed data (fallback when DB has no live narratives) ─────────────────────

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


# ── Live data loader (patchable — replaces seed in Phase 8) ─────────────────


async def fetch_latest_narratives() -> list[dict[str, Any]]:
    """Load the most recent narratives from the database.

    In production this queries the ``narratives`` table (populated by the
    NarrativeDetector pipeline).  Returns an empty list when the table is
    empty or the DB is unavailable — the endpoint then falls back to seed
    data.

    Returns:
        List of narrative dicts compatible with ``NarrativeResponse``.
    """
    try:
        from sqlalchemy import text  # noqa: PLC0415
        from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415

        from app.config import settings  # noqa: PLC0415

        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            # Query latest snapshot date
            result = await conn.execute(
                text(
                    "SELECT id, name, momentum_score, trend, keywords, "
                    "token_symbols, snapshot_date "
                    "FROM narratives "
                    "ORDER BY snapshot_date DESC, momentum_score DESC "
                    "LIMIT 20"
                )
            )
            rows = result.fetchall()

        if not rows:
            return []

        narratives: list[dict[str, Any]] = []
        for row in rows:
            keywords = row.keywords if isinstance(row.keywords, list) else []
            tokens = row.token_symbols if isinstance(row.token_symbols, list) else []
            narratives.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "momentum_score": float(row.momentum_score),
                    "trend": row.trend,
                    "tokens": tokens,
                    "keywords": keywords,
                    "token_count": len(tokens),
                }
            )
        return narratives

    except Exception:
        logger.warning("narratives.db_fetch_failed")
        return []


# ── Endpoint ───────────────────────────────────────────────────────────────


@router.get("/", response_model=list[NarrativeResponse])
async def get_narratives() -> list[NarrativeResponse]:
    """Return the list of active narrative clusters.

    Phase 8 behaviour:
    1. Try to load live narratives from the DB (populated by NarrativeDetector).
    2. If the DB returns no rows, fall back to curated seed data.

    Returns:
        List of NarrativeResponse objects sorted by momentum_score desc.
    """
    live = await fetch_latest_narratives()
    if live:
        logger.info("narratives.list.live", count=len(live))
        parsed = [NarrativeResponse(**n) for n in live]
        return sorted(parsed, key=lambda n: n.momentum_score, reverse=True)

    logger.info("narratives.list.seed", count=len(_SEED_NARRATIVES))
    return sorted(_SEED_NARRATIVES, key=lambda n: n.momentum_score, reverse=True)
