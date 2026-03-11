"""Rankings route handlers — GET /rankings/opportunities."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.score import TokenScore
from app.models.token import Token

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class OpportunityRankItem(BaseModel):
    """Single entry in the opportunity ranking."""

    symbol: str
    name: str
    coingecko_id: str
    fundamental_score: float
    opportunity_score: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/opportunities", response_model=list[OpportunityRankItem])
async def get_opportunities(
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[OpportunityRankItem]:
    """Return tokens ranked by opportunity score, highest first."""
    stmt = (
        select(Token, TokenScore)
        .join(TokenScore, TokenScore.token_id == Token.id)
        .order_by(TokenScore.opportunity_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        OpportunityRankItem(
            symbol=token.symbol,
            name=token.name,
            coingecko_id=token.coingecko_id,
            fundamental_score=score.fundamental_score,
            opportunity_score=score.opportunity_score,
        )
        for token, score in rows
    ]


# Keep the dependency importable for test overrides
__all__ = ["router", "get_db"]
