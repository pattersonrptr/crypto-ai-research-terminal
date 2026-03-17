"""Rankings route handlers — GET /rankings/opportunities, GET /rankings/categories."""

from enum import Enum
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.market_data import MarketData
from app.models.score import TokenScore
from app.models.token import Token
from app.scoring.token_filter import TokenFilter

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]

# Module-level filter instance — shared across requests (volume-based filtering only).
_token_filter = TokenFilter()


# ---------------------------------------------------------------------------
# Enums for validated query params
# ---------------------------------------------------------------------------


class SortColumn(str, Enum):
    """Allowed columns for server-side sorting."""

    opportunity_score = "opportunity_score"
    fundamental_score = "fundamental_score"
    technology_score = "technology_score"
    tokenomics_score = "tokenomics_score"
    adoption_score = "adoption_score"
    dev_activity_score = "dev_activity_score"
    narrative_score = "narrative_score"
    growth_score = "growth_score"
    risk_score = "risk_score"
    listing_probability = "listing_probability"
    cycle_leader_prob = "cycle_leader_prob"
    market_cap = "market_cap"
    volume_24h = "volume_24h"
    token_name = "name"  # noqa: S105
    token_rank = "rank"  # noqa: S105


class SortOrder(str, Enum):
    """Sort direction."""

    asc = "asc"
    desc = "desc"


# Mapping from SortColumn to the actual SQLAlchemy column expression.
_SORT_COLUMN_MAP: dict[SortColumn, object] = {
    SortColumn.opportunity_score: TokenScore.opportunity_score,
    SortColumn.fundamental_score: TokenScore.fundamental_score,
    SortColumn.technology_score: TokenScore.technology_score,
    SortColumn.tokenomics_score: TokenScore.tokenomics_score,
    SortColumn.adoption_score: TokenScore.adoption_score,
    SortColumn.dev_activity_score: TokenScore.dev_activity_score,
    SortColumn.narrative_score: TokenScore.narrative_score,
    SortColumn.growth_score: TokenScore.growth_score,
    SortColumn.risk_score: TokenScore.risk_score,
    SortColumn.listing_probability: TokenScore.listing_probability,
    SortColumn.cycle_leader_prob: TokenScore.cycle_leader_prob,
    SortColumn.market_cap: MarketData.market_cap_usd,
    SortColumn.volume_24h: MarketData.volume_24h_usd,
    SortColumn.token_name: Token.name,
    SortColumn.token_rank: MarketData.rank,
}


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


class PaginatedRankingsResponse(BaseModel):
    """Paginated response wrapping ranking items with total count."""

    data: list[RankingOpportunitySchema]
    total_count: int


class CategoryCountSchema(BaseModel):
    """A distinct category with its token count."""

    category: str
    count: int


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


def _base_query() -> Select[Any]:
    """Build the base SELECT joining Token → latest TokenScore → latest MarketData."""
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

    return (
        select(Token, TokenScore, MarketData)
        .join(TokenScore, TokenScore.token_id == Token.id)
        .join(latest_score_sq, TokenScore.id == latest_score_sq.c.max_id)
        .outerjoin(MarketData, MarketData.token_id == Token.id)
        .outerjoin(latest_md_sq, MarketData.id == latest_md_sq.c.max_id)
        .where((MarketData.id == None) | (latest_md_sq.c.max_id != None))  # noqa: E711
    )


def _apply_filters(
    stmt: Select[Any],
    *,
    categories: str | None,
    exclude_categories: str | None,
    search: str | None,
) -> Select[Any]:
    """Apply category + search WHERE clauses to the statement."""
    if categories:
        cat_list = [c.strip().lower() for c in categories.split(",") if c.strip()]
        if cat_list:
            stmt = stmt.where(func.lower(Token.category).in_(cat_list))

    if exclude_categories:
        exc_list = [c.strip().lower() for c in exclude_categories.split(",") if c.strip()]
        if exc_list:
            stmt = stmt.where(
                or_(
                    Token.category == None,  # noqa: E711
                    ~func.lower(Token.category).in_(exc_list),
                )
            )

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Token.symbol.ilike(pattern),
                Token.name.ilike(pattern),
            )
        )

    return stmt


def _apply_sorting(
    stmt: Select[Any],
    *,
    sort: SortColumn,
    order: SortOrder,
) -> Select[Any]:
    """Apply ORDER BY clause based on sort column and direction."""
    col: Any = _SORT_COLUMN_MAP[sort]
    direction = col.desc() if order == SortOrder.desc else col.asc()
    return stmt.order_by(direction)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/opportunities", response_model=PaginatedRankingsResponse)
async def get_opportunities(
    db: DbDep,
    categories: str | None = Query(
        default=None, description="Comma-separated categories to include"
    ),
    exclude_categories: str | None = Query(
        default=None, description="Comma-separated categories to exclude"
    ),
    sort: SortColumn = Query(
        default=SortColumn.opportunity_score, description="Column to sort by"
    ),
    order: SortOrder = Query(
        default=SortOrder.desc, description="Sort direction"
    ),
    search: str | None = Query(
        default=None, description="Search symbol or name (case-insensitive)"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=50, ge=1, le=500, description="Items per page"
    ),
) -> PaginatedRankingsResponse:
    """Return tokens ranked with server-side filtering, sorting, and pagination.

    Uses only the **latest** TokenScore and MarketData per token
    (by highest ``id``), so successive collection runs never produce
    duplicate rows in the response.
    """

    # Build base query with latest score/market data joins
    stmt = _base_query()

    # Apply server-side filters (category, search)
    stmt = _apply_filters(
        stmt, categories=categories, exclude_categories=exclude_categories, search=search
    )

    # Apply sorting
    stmt = _apply_sorting(stmt, sort=sort, order=order)

    # Execute full query (no pagination yet) for post-query volume filtering + count
    result = await db.execute(stmt)
    rows: list[Any] = list(result.all())

    # Post-query filtering: remove dead tokens (no/low volume).
    # Category-based filtering is now done server-side in SQL.
    filtered: list[tuple[Token, TokenScore, MarketData | None]] = []
    for token, score, md in rows:
        volume = md.volume_24h_usd if md is not None else None
        if _token_filter.is_dead(volume_24h=volume):
            continue
        filtered.append((token, score, md))

    total_count = len(filtered)

    # Apply pagination in Python (after volume filtering)
    offset = (page - 1) * page_size
    page_items = filtered[offset : offset + page_size]

    logger.info(
        "rankings.opportunities.fetched",
        total=len(rows),
        after_filter=total_count,
        page=page,
        page_size=page_size,
        returned=len(page_items),
    )

    data = [
        RankingOpportunitySchema(
            rank=offset + idx + 1,
            token=TokenWithScoreSchema(
                id=token.id,
                symbol=token.symbol,
                name=token.name,
                coingecko_id=token.coingecko_id,
                category=token.category,
                created_at=str(token.created_at),
                updated_at=str(token.created_at),
                rank=md.rank if md is not None and md.rank else offset + idx + 1,
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
        for idx, (token, score, md) in enumerate(page_items)
    ]

    return PaginatedRankingsResponse(data=data, total_count=total_count)


@router.get("/categories", response_model=list[CategoryCountSchema])
async def get_categories(db: DbDep) -> list[CategoryCountSchema]:
    """Return all distinct token categories with their token counts.

    Null categories are excluded. Results sorted by count descending.
    """
    stmt = (
        select(Token.category, func.count(Token.id).label("count"))
        .where(Token.category != None)  # noqa: E711
        .group_by(Token.category)
        .order_by(func.count(Token.id).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        CategoryCountSchema(category=cat, count=cnt)
        for cat, cnt in rows
    ]


# Keep the dependency importable for test overrides
__all__ = ["router", "get_db"]
