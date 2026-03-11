"""Token route handlers — GET /tokens and GET /tokens/{symbol}."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.token import Token

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """Public representation of a Token."""

    id: int
    symbol: str
    name: str
    coingecko_id: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[TokenResponse])
async def get_tokens(db: DbDep) -> list[Token]:
    """Return all tracked tokens."""
    result = await db.execute(select(Token).order_by(Token.symbol))
    return list(result.scalars().all())


@router.get("/{symbol}", response_model=TokenResponse)
async def get_token_by_symbol(symbol: str, db: DbDep) -> Token:
    """Return a single token by its symbol, or 404 if not found."""
    result = await db.execute(select(Token).where(Token.symbol == symbol.upper()))
    token = result.scalar_one_or_none()
    if token is None:
        raise HTTPException(status_code=404, detail=f"Token '{symbol}' not found.")
    return token


# Keep the dependency importable for test overrides (re-exported from session)
__all__ = ["router", "get_db"]
