"""Narratives route handlers.

Provides endpoints for viewing detected market narratives:
- GET /narratives - List all active narrative clusters

Loads live narratives from the DB (populated by NarrativePersister in the
daily pipeline).  Returns an empty list when no narratives have been
persisted yet.
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


# ── Live data loader ────────────────────────────────────────────────────────


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
            # Query only the latest snapshot date to avoid duplicates
            result = await conn.execute(
                text(
                    "SELECT id, name, momentum_score, trend, keywords, "
                    "token_symbols, snapshot_date "
                    "FROM narratives "
                    "WHERE snapshot_date = ("
                    "  SELECT MAX(snapshot_date) FROM narratives"
                    ") "
                    "ORDER BY momentum_score DESC"
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

    Loads live narratives from the DB (populated by the daily pipeline via
    ``NarrativePersister``).  Returns an empty list when no narratives have
    been persisted yet.

    Returns:
        List of NarrativeResponse objects sorted by momentum_score desc.
    """
    live = await fetch_latest_narratives()
    if live:
        logger.info("narratives.list.live", count=len(live))
        parsed = [NarrativeResponse(**n) for n in live]
        return sorted(parsed, key=lambda n: n.momentum_score, reverse=True)

    logger.info("narratives.list.empty")
    return []
