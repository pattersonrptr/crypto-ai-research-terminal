"""Weight service — load/persist active scoring weights with Redis cache.

Provides :func:`get_active_weights` and :func:`apply_weights_to_db` to
read/write the active pillar weight configuration from the ``scoring_weights``
table, with an optional Redis cache layer (5 minute TTL).

If no active row exists in the DB, Phase 9 defaults are returned.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from app.models.scoring_weight import ScoringWeight

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Rebalanced defaults — risk-heavy to properly penalise speculative tokens.
DEFAULT_WEIGHTS: dict[str, float] = {
    "fundamental": 0.25,
    "growth": 0.20,
    "narrative": 0.15,
    "listing": 0.10,
    "risk": 0.30,
}

_CACHE_KEY = "scoring:active_weights"
_CACHE_TTL_SECONDS = 300  # 5 minutes


async def get_active_weights(
    *,
    session: AsyncSession,
    redis: Any | None = None,
) -> dict[str, Any]:
    """Return the currently active pillar weights.

    Lookup order:
    1. Redis cache (key ``scoring:active_weights``, 5 min TTL).
    2. ``scoring_weights`` table — row with ``is_active=True``.
    3. Hardcoded Phase 9 defaults.

    Args:
        session: Async SQLAlchemy session for DB access.
        redis: Optional ``redis.asyncio.Redis`` client for caching.

    Returns:
        Dict with keys ``fundamental``, ``growth``, ``narrative``,
        ``listing``, ``risk``, and ``source``.
    """
    # 1. Try Redis cache
    if redis is not None:
        try:
            cached = await redis.get(_CACHE_KEY)
            if cached is not None:
                logger.debug("weight_service.cache_hit")
                return json.loads(cached)  # type: ignore[no-any-return]
        except Exception:
            logger.warning("weight_service.redis_error", exc_info=True)

    # 2. Query DB
    stmt = select(ScoringWeight).where(ScoringWeight.is_active.is_(True))
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()

    if row is not None:
        weights: dict[str, Any] = {
            "fundamental": row.fundamental,
            "growth": row.growth,
            "narrative": row.narrative,
            "listing": row.listing,
            "risk": row.risk,
            "source": "calibrated",
        }
    else:
        weights = {**DEFAULT_WEIGHTS, "source": "default_phase9"}

    # 3. Cache in Redis
    if redis is not None:
        try:
            await redis.setex(_CACHE_KEY, _CACHE_TTL_SECONDS, json.dumps(weights))
            logger.debug("weight_service.cache_set")
        except Exception:
            logger.warning("weight_service.redis_set_error", exc_info=True)

    return weights


async def apply_weights_to_db(
    *,
    session: AsyncSession,
    fundamental: float,
    growth: float,
    narrative: float,
    listing: float,
    risk: float,
    source_cycle: str | None = None,
    precision_at_k: float | None = None,
    k: int | None = None,
    redis: Any | None = None,
) -> dict[str, Any]:
    """Persist new active weights and deactivate the previous active row.

    Args:
        session: Async SQLAlchemy session.
        fundamental: Weight for fundamental sub-score.
        growth: Weight for growth sub-score.
        narrative: Weight for narrative sub-score.
        listing: Weight for listing sub-score.
        risk: Weight for risk sub-score.
        source_cycle: Optional cycle name that produced these weights.
        precision_at_k: Optional best precision achieved.
        k: Optional K value used during calibration.
        redis: Optional Redis client — cache will be invalidated.

    Returns:
        Dict with the applied weights and metadata.
    """
    # Deactivate previous active row (if any)
    stmt = select(ScoringWeight).where(ScoringWeight.is_active.is_(True))
    result = await session.execute(stmt)
    previous = result.scalar_one_or_none()
    if previous is not None:
        previous.is_active = False
        logger.info("weight_service.deactivated_previous", id=previous.id)

    # Insert new active row
    new_row = ScoringWeight(
        fundamental=fundamental,
        growth=growth,
        narrative=narrative,
        listing=listing,
        risk=risk,
        source_cycle=source_cycle,
        precision_at_k=precision_at_k,
        k=k,
        is_active=True,
    )
    session.add(new_row)
    await session.commit()

    logger.info(
        "weight_service.applied",
        fundamental=fundamental,
        growth=growth,
        narrative=narrative,
        listing=listing,
        risk=risk,
        source_cycle=source_cycle,
    )

    # Invalidate cache
    await invalidate_weight_cache(redis=redis)

    return {
        "fundamental": fundamental,
        "growth": growth,
        "narrative": narrative,
        "listing": listing,
        "risk": risk,
        "source_cycle": source_cycle,
        "precision_at_k": precision_at_k,
        "k": k,
    }


async def invalidate_weight_cache(*, redis: Any | None = None) -> None:
    """Delete the active weights cache key from Redis.

    Args:
        redis: Optional Redis client. No-op when ``None``.
    """
    if redis is None:
        return
    try:
        await redis.delete(_CACHE_KEY)
        logger.debug("weight_service.cache_invalidated")
    except Exception:
        logger.warning("weight_service.cache_invalidate_error", exc_info=True)
