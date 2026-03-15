"""Summary route handlers — GET /tokens/{symbol}/summary.

Serves cached AI-generated summaries from the ``ai_analyses`` table.
If no cached summary exists, returns 404 with a message suggesting
the user wait for the next analysis run.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.summary_cache_service import SummaryCacheService
from app.db.session import get_db
from app.models.ai_analysis import AiAnalysis
from app.models.token import Token

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]

_cache_service = SummaryCacheService(cache_ttl_hours=24.0)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class SummaryResponse(BaseModel):
    """AI-generated summary response."""

    summary_text: str
    key_strengths: list[str]
    key_risks: list[str]
    investment_thesis: str
    target_audience: str
    model_used: str
    generated_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{symbol}/summary", response_model=SummaryResponse)
async def get_token_summary(symbol: str, db: DbDep) -> SummaryResponse:
    """Return the cached AI summary for a token, or 404 if none exists.

    The summary is generated asynchronously by the daily pipeline and
    cached in the ``ai_analyses`` table.  This endpoint only reads the
    cache — it does **not** trigger LLM calls.
    """
    # Look up token
    stmt = select(Token).where(Token.symbol == symbol.upper())
    result = await db.execute(stmt)
    token = result.scalars().first()
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{symbol}' not found.")

    # Look up latest cached summary
    stmt_analysis = (
        select(AiAnalysis)
        .where(AiAnalysis.token_id == token.id)
        .where(AiAnalysis.analysis_type == "summary")
        .order_by(AiAnalysis.created_at.desc())
        .limit(1)
    )
    result_analysis = await db.execute(stmt_analysis)
    analysis = result_analysis.scalars().first()

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"No summary available for '{symbol}'. "
            "It will be generated in the next analysis run.",
        )

    summary = _cache_service.parse_cached(analysis)
    return SummaryResponse(
        summary_text=summary.summary_text,
        key_strengths=summary.key_strengths,
        key_risks=summary.key_risks,
        investment_thesis=summary.investment_thesis,
        target_audience=summary.target_audience,
        model_used=analysis.model_used,
        generated_at=str(analysis.created_at),
    )
