"""Rankings route handlers — GET /rankings/opportunities."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.score import TokenScore
from app.models.token import Token

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Response schemas (mirror frontend TokenWithScore + RankingOpportunity)
# ---------------------------------------------------------------------------


class TokenScoreSchema(BaseModel):
    """Detailed score breakdown for a token."""

    fundamental_score: float
    technology_score: float = 0.0
    tokenomics_score: float = 0.0
    adoption_score: float = 0.0
    dev_activity_score: float = 0.0
    narrative_score: float = 0.0
    growth_score: float = 0.0
    risk_score: float = 0.0
    listing_probability: float = 0.0
    cycle_leader_prob: float = 0.0
    opportunity_score: float
    snapshot_date: str = ""


class TokenWithScoreSchema(BaseModel):
    """Full token representation with latest score and market data."""

    id: int
    symbol: str
    name: str
    coingecko_id: str | None = None
    category: str | None = None
    github_repo: str | None = None
    whitepaper_url: str | None = None
    created_at: str = ""
    updated_at: str = ""
    latest_score: TokenScoreSchema | None = None
    price_usd: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    price_change_7d: float | None = None
    rank: int | None = None


class RankingOpportunitySchema(BaseModel):
    """Single entry in the opportunity ranking (matches frontend RankingOpportunity)."""

    rank: int
    token: TokenWithScoreSchema
    signals: list[str]

    # Keep flat fields for backwards compatibility with older clients
    symbol: str
    name: str
    coingecko_id: str
    fundamental_score: float
    opportunity_score: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_signals(score: TokenScore) -> list[str]:
    """Generate human-readable signal labels from a score object."""
    signals: list[str] = []
    if score.opportunity_score >= 0.8:
        signals.append("High opportunity score")
    if score.fundamental_score >= 0.8:
        signals.append("Strong fundamentals")
    return signals or ["Listed on radar"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/opportunities", response_model=list[RankingOpportunitySchema])
async def get_opportunities(
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RankingOpportunitySchema]:
    """Return tokens ranked by opportunity score, highest first."""
    stmt = (
        select(Token, TokenScore)
        .join(TokenScore, TokenScore.token_id == Token.id)
        .order_by(TokenScore.opportunity_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    logger.info("rankings.opportunities.fetched", count=len(rows))

    return [
        RankingOpportunitySchema(
            rank=idx + 1,
            token=TokenWithScoreSchema(
                id=token.id,
                symbol=token.symbol,
                name=token.name,
                coingecko_id=token.coingecko_id,
                created_at=str(token.created_at),
                updated_at=str(token.created_at),
                rank=idx + 1,
                latest_score=TokenScoreSchema(
                    fundamental_score=score.fundamental_score,
                    opportunity_score=score.opportunity_score,
                    snapshot_date=str(score.scored_at),
                ),
            ),
            signals=_build_signals(score),
            # flat backwards-compat fields
            symbol=token.symbol,
            name=token.name,
            coingecko_id=token.coingecko_id,
            fundamental_score=score.fundamental_score,
            opportunity_score=score.opportunity_score,
        )
        for idx, (token, score) in enumerate(rows)
    ]


# Keep the dependency importable for test overrides
__all__ = ["router", "get_db"]
