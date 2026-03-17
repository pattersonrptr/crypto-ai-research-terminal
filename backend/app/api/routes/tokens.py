"""Token route handlers — GET /tokens, GET /tokens/{symbol}, GET /tokens/{symbol}/explanation."""

from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.social_data import SocialData
from app.models.token import Token
from app.scoring.score_explainer import ScoreExplainer

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


class PillarExplanationSchema(BaseModel):
    """Schema for a single pillar explanation."""

    pillar: str
    score: float
    explanation: str


class TokenExplanationSchema(BaseModel):
    """Schema for GET /tokens/{symbol}/explanation response."""

    symbol: str
    name: str
    opportunity_score: float
    explanations: list[PillarExplanationSchema]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_token_schema(
    token: Token,
    score: TokenScore | None,
    market_data: MarketData | None = None,
    rank: int | None = None,
) -> TokenWithScoreSchema:
    """Map ORM objects to the response schema."""
    return TokenWithScoreSchema(
        id=token.id,
        symbol=token.symbol,
        name=token.name,
        coingecko_id=token.coingecko_id,
        created_at=str(token.created_at),
        updated_at=str(token.created_at),
        rank=market_data.rank if market_data is not None and market_data.rank else rank,
        price_usd=market_data.price_usd if market_data is not None else None,
        market_cap=market_data.market_cap_usd if market_data is not None else None,
        volume_24h=market_data.volume_24h_usd if market_data is not None else None,
        latest_score=(
            TokenScoreSchema(
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
            if score is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[TokenWithScoreSchema])
async def get_tokens(db: DbDep) -> list[TokenWithScoreSchema]:
    """Return all tracked tokens, joined with their latest score and market data."""

    # Subqueries: pick only the newest row per token
    latest_score_sq = (
        select(func.max(TokenScore.id).label("max_id"))
        .group_by(TokenScore.token_id)
        .subquery("latest_score")
    )
    latest_md_sq = (
        select(func.max(MarketData.id).label("max_id"))
        .group_by(MarketData.token_id)
        .subquery("latest_md")
    )

    stmt = (
        select(Token, TokenScore, MarketData)
        .outerjoin(TokenScore, TokenScore.token_id == Token.id)
        .outerjoin(latest_score_sq, TokenScore.id == latest_score_sq.c.max_id)
        .outerjoin(MarketData, MarketData.token_id == Token.id)
        .outerjoin(latest_md_sq, MarketData.id == latest_md_sq.c.max_id)
        .where(
            # Keep only the latest score (or no score at all)
            (TokenScore.id == None) | (latest_score_sq.c.max_id != None)  # noqa: E711
        )
        .where(
            # Keep only the latest market data (or no market data at all)
            (MarketData.id == None) | (latest_md_sq.c.max_id != None)  # noqa: E711
        )
        .order_by(Token.symbol)
    )
    result = await db.execute(stmt)
    rows = result.all()
    logger.info("tokens.list.fetched", count=len(rows))
    return [_build_token_schema(token, score, md) for token, score, md in rows]


@router.get("/{symbol}", response_model=TokenWithScoreSchema)
async def get_token_by_symbol(symbol: str, db: DbDep) -> TokenWithScoreSchema:
    """Return a single token by its symbol (with latest score + market data), or 404."""

    # Subqueries: pick only the newest row per token
    latest_score_sq = (
        select(func.max(TokenScore.id).label("max_id"))
        .group_by(TokenScore.token_id)
        .subquery("latest_score")
    )
    latest_md_sq = (
        select(func.max(MarketData.id).label("max_id"))
        .group_by(MarketData.token_id)
        .subquery("latest_md")
    )

    stmt = (
        select(Token, TokenScore, MarketData)
        .outerjoin(TokenScore, TokenScore.token_id == Token.id)
        .outerjoin(latest_score_sq, TokenScore.id == latest_score_sq.c.max_id)
        .outerjoin(MarketData, MarketData.token_id == Token.id)
        .outerjoin(latest_md_sq, MarketData.id == latest_md_sq.c.max_id)
        .where(Token.symbol == symbol.upper())
        .where(
            (TokenScore.id == None) | (latest_score_sq.c.max_id != None)  # noqa: E711
        )
        .where(
            (MarketData.id == None) | (latest_md_sq.c.max_id != None)  # noqa: E711
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Token '{symbol}' not found.")
    token, score, md = row
    return _build_token_schema(token, score, md)


# ---------------------------------------------------------------------------
# Token detail helpers
# ---------------------------------------------------------------------------


async def _fetch_token_with_details(
    symbol: str, db: AsyncSession
) -> tuple[Token, TokenScore | None, MarketData | None, SocialData | None] | None:
    """Fetch token, latest score, market data, and social data.

    Returns:
        Tuple of (token, score, market_data, social_data) or ``None``
        if the token is not found.
    """
    latest_score_sq = (
        select(func.max(TokenScore.id).label("max_id"))
        .group_by(TokenScore.token_id)
        .subquery("latest_score")
    )
    latest_md_sq = (
        select(func.max(MarketData.id).label("max_id"))
        .group_by(MarketData.token_id)
        .subquery("latest_md")
    )
    latest_sd_sq = (
        select(func.max(SocialData.id).label("max_id"))
        .group_by(SocialData.token_id)
        .subquery("latest_sd")
    )

    stmt = (
        select(Token, TokenScore, MarketData, SocialData)
        .outerjoin(TokenScore, TokenScore.token_id == Token.id)
        .outerjoin(latest_score_sq, TokenScore.id == latest_score_sq.c.max_id)
        .outerjoin(MarketData, MarketData.token_id == Token.id)
        .outerjoin(latest_md_sq, MarketData.id == latest_md_sq.c.max_id)
        .outerjoin(SocialData, SocialData.token_id == Token.id)
        .outerjoin(latest_sd_sq, SocialData.id == latest_sd_sq.c.max_id)
        .where(Token.symbol == symbol.upper())
        .where(
            (TokenScore.id == None) | (latest_score_sq.c.max_id != None)  # noqa: E711
        )
        .where(
            (MarketData.id == None) | (latest_md_sq.c.max_id != None)  # noqa: E711
        )
        .where(
            (SocialData.id == None) | (latest_sd_sq.c.max_id != None)  # noqa: E711
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        return None
    return row[0], row[1], row[2], row[3]


def _build_explainer_data(
    token: Token,
    score: TokenScore,
    md: MarketData | None,
    sd: SocialData | None,
) -> dict[str, Any]:
    """Build the dict that ScoreExplainer.explain() expects."""
    data: dict[str, Any] = {
        "symbol": token.symbol,
        "name": token.name,
        "fundamental_score": score.fundamental_score,
        "technology_score": score.technology_score,
        "tokenomics_score": score.tokenomics_score,
        "adoption_score": score.adoption_score,
        "dev_activity_score": score.dev_activity_score,
        "narrative_score": score.narrative_score,
        "growth_score": score.growth_score,
        "risk_score": score.risk_score,
        "listing_probability": score.listing_probability,
        "cycle_leader_prob": score.cycle_leader_prob,
        "opportunity_score": score.opportunity_score,
    }
    if md is not None:
        data["price_usd"] = md.price_usd
        data["market_cap_usd"] = md.market_cap_usd
        data["volume_24h_usd"] = md.volume_24h_usd
        data["price_change_7d"] = getattr(md, "price_change_7d", None)
    if sd is not None:
        data["reddit_subscribers"] = sd.reddit_subscribers
        data["reddit_posts_24h"] = sd.reddit_posts_24h
        data["sentiment_score"] = sd.sentiment_score
        data["twitter_mentions_24h"] = sd.twitter_mentions_24h
        data["twitter_engagement"] = sd.twitter_engagement
    return data


@router.get(
    "/{symbol}/explanation",
    response_model=TokenExplanationSchema,
)
async def get_token_explanation(symbol: str, db: DbDep) -> TokenExplanationSchema:
    """Return a human-readable score explanation for a token, or 404."""
    details = await _fetch_token_with_details(symbol, db)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Token '{symbol}' not found.")

    token, score, md, sd = details
    if score is None:
        raise HTTPException(
            status_code=404,
            detail=f"No scores available for '{symbol}'.",
        )

    explainer_data = _build_explainer_data(token, score, md, sd)
    explanations = ScoreExplainer.explain(explainer_data)

    return TokenExplanationSchema(
        symbol=token.symbol,
        name=token.name,
        opportunity_score=score.opportunity_score,
        explanations=[PillarExplanationSchema(**e.to_dict()) for e in explanations],
    )


# Keep the dependency importable for test overrides (re-exported from session)
__all__ = ["router", "get_db"]
