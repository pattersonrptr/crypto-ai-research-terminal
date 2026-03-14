"""Token route handlers — GET /tokens and GET /tokens/{symbol}."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
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
# Response schemas (mirror frontend TokenWithScore interface)
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
    """Full token representation with optional latest score and market data."""

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_token_schema(token: Token, score: TokenScore | None, rank: int | None = None) -> TokenWithScoreSchema:
    """Map ORM objects to the response schema."""
    return TokenWithScoreSchema(
        id=token.id,
        symbol=token.symbol,
        name=token.name,
        coingecko_id=token.coingecko_id,
        created_at=str(token.created_at),
        updated_at=str(token.created_at),
        rank=rank,
        latest_score=(
            TokenScoreSchema(
                fundamental_score=score.fundamental_score,
                opportunity_score=score.opportunity_score,
                snapshot_date=str(score.scored_at),
            )
            if score is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[TokenWithScoreSchema])
async def get_tokens(db: DbDep) -> list[TokenWithScoreSchema]:
    """Return all tracked tokens, joined with their latest score when available."""
    stmt = (
        select(Token, TokenScore)
        .outerjoin(TokenScore, TokenScore.token_id == Token.id)
        .order_by(Token.symbol)
    )
    result = await db.execute(stmt)
    rows = result.all()
    logger.info("tokens.list.fetched", count=len(rows))
    return [_build_token_schema(token, score) for token, score in rows]


@router.get("/{symbol}", response_model=TokenWithScoreSchema)
async def get_token_by_symbol(symbol: str, db: DbDep) -> TokenWithScoreSchema:
    """Return a single token by its symbol (with latest score), or 404."""
    stmt = (
        select(Token, TokenScore)
        .outerjoin(TokenScore, TokenScore.token_id == Token.id)
        .where(Token.symbol == symbol.upper())
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Token '{symbol}' not found.")
    token, score = row
    return _build_token_schema(token, score)


# Keep the dependency importable for test overrides (re-exported from session)
__all__ = ["router", "get_db"]
