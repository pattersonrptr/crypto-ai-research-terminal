"""Rankings route handlers — GET /rankings/opportunities."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from app.scoring.token_filter import TokenFilter

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]

# Module-level filter instance — shared across requests.
_token_filter = TokenFilter()


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


def _build_score_schema(score: TokenScore) -> TokenScoreSchema:
    """Map all 11 sub-scores from a TokenScore ORM object."""
    return TokenScoreSchema(
        fundamental_score=score.fundamental_score,
        opportunity_score=score.opportunity_score,
        technology_score=score.technology_score,
        tokenomics_score=score.tokenomics_score,
        adoption_score=score.adoption_score,
        dev_activity_score=score.dev_activity_score,
        narrative_score=score.narrative_score,
        growth_score=score.growth_score,
        risk_score=score.risk_score,
        listing_probability=score.listing_probability,
        cycle_leader_prob=score.cycle_leader_prob,
        snapshot_date=str(score.scored_at),
    )


def _build_signals(score: TokenScore) -> list[str]:
    """Generate human-readable signal labels from a score object."""
    signals: list[str] = []
    if score.opportunity_score >= 0.8:
        signals.append("High opportunity score")
    if score.fundamental_score >= 0.8:
        signals.append("Strong fundamentals")
    if score.growth_score >= 0.7:
        signals.append("Strong growth momentum")
    if score.risk_score >= 0.8:
        signals.append("Low risk profile")
    if score.narrative_score >= 0.7:
        signals.append("Strong narrative trend")
    if score.listing_probability >= 0.8:
        signals.append("High listing coverage")
    return signals or ["Listed on radar"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/opportunities", response_model=list[RankingOpportunitySchema])
async def get_opportunities(
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RankingOpportunitySchema]:
    """Return tokens ranked by opportunity score, highest first.

    Uses only the **latest** TokenScore and MarketData per token
    (by highest ``id``), so successive collection runs never produce
    duplicate rows in the response.
    """

    # Subquery: latest TokenScore.id per token
    latest_score_sq = (
        select(func.max(TokenScore.id).label("max_id"))
        .group_by(TokenScore.token_id)
        .subquery("latest_score")
    )

    # Subquery: latest MarketData.id per token
    latest_md_sq = (
        select(func.max(MarketData.id).label("max_id"))
        .group_by(MarketData.token_id)
        .subquery("latest_md")
    )

    stmt = (
        select(Token, TokenScore, MarketData)
        .join(TokenScore, TokenScore.token_id == Token.id)
        .join(latest_score_sq, TokenScore.id == latest_score_sq.c.max_id)
        .outerjoin(MarketData, MarketData.token_id == Token.id)
        .outerjoin(latest_md_sq, MarketData.id == latest_md_sq.c.max_id)
        .where((MarketData.id == None) | (latest_md_sq.c.max_id != None))  # noqa: E711
        .order_by(TokenScore.opportunity_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Post-query filtering: remove stablecoins, wrapped tokens, and dead projects.
    filtered: list[tuple[Token, TokenScore, MarketData | None]] = []
    for token, score, md in rows:
        volume = md.volume_24h_usd if md is not None else None
        if _token_filter.should_exclude(symbol=token.symbol, volume_24h=volume):
            continue
        filtered.append((token, score, md))

    logger.info(
        "rankings.opportunities.fetched",
        total=len(rows),
        after_filter=len(filtered),
    )

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
                rank=md.rank if md is not None and md.rank else idx + 1,
                price_usd=md.price_usd if md is not None else None,
                market_cap=md.market_cap_usd if md is not None else None,
                volume_24h=md.volume_24h_usd if md is not None else None,
                latest_score=_build_score_schema(score),
            ),
            signals=_build_signals(score),
            # flat backwards-compat fields
            symbol=token.symbol,
            name=token.name,
            coingecko_id=token.coingecko_id,
            fundamental_score=score.fundamental_score,
            opportunity_score=score.opportunity_score,
        )
        for idx, (token, score, md) in enumerate(filtered)
    ]


# Keep the dependency importable for test overrides
__all__ = ["router", "get_db"]
