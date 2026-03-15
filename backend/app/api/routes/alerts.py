"""Alerts route handlers — persisted to PostgreSQL.

Provides endpoints for managing and viewing alerts:
- GET /alerts — List all alerts with filtering
- GET /alerts/stats — Get alert statistics
- GET /alerts/{id} — Get single alert
- POST /alerts/test — Send test alert via Telegram
- PUT /alerts/{id}/acknowledge — Acknowledge alert
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.telegram_bot import TelegramBot
from app.config import settings
from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


# --- Pydantic response models ---


class AlertResponse(BaseModel):
    """Alert response schema (matches frontend ``Alert`` interface)."""

    id: int
    token_id: int | None = None
    alert_type: str
    message: str
    metadata: dict[str, Any] | None = None
    sent_telegram: bool = False
    acknowledged: bool = False
    created_at: str  # ISO-8601

    model_config = {"from_attributes": True}


class AlertStatsResponse(BaseModel):
    """Alert statistics response schema."""

    total: int
    unacknowledged: int
    by_type: dict[str, int]


class TestAlertRequest(BaseModel):
    """Request schema for test alert."""

    message: str = Field(..., min_length=1, description="Test message to send")


class TestAlertResponse(BaseModel):
    """Response schema for test alert."""

    success: bool
    message: str


class AcknowledgeResponse(BaseModel):
    """Response schema for acknowledge endpoint."""

    id: int
    acknowledged: bool
    acknowledged_at: str  # ISO-8601


# --- Helpers ---


def _alert_to_response(alert: Alert) -> dict[str, Any]:
    """Convert an Alert ORM object to a response dict."""
    return {
        "id": alert.id,
        "token_id": alert.token_id,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "metadata": alert.alert_metadata,
        "sent_telegram": alert.sent_telegram or False,
        "acknowledged": alert.acknowledged or False,
        "created_at": (alert.triggered_at.isoformat() if alert.triggered_at else ""),
    }


# --- Route handlers ---


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200, description="Max alerts to return"),
    alert_type: str | None = Query(default=None, description="Filter by alert type"),
    acknowledged: bool | None = Query(default=None, description="Filter by ack status"),
) -> list[dict[str, Any]]:
    """Get list of alerts with optional filtering.

    Args:
        db: Async database session (injected).
        limit: Maximum number of alerts to return.
        alert_type: Optional filter by alert type.
        acknowledged: Optional filter by acknowledged status.

    Returns:
        List of alerts matching the criteria.
    """
    stmt = select(Alert)

    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)

    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged == acknowledged)

    stmt = stmt.order_by(Alert.triggered_at.desc()).limit(limit)

    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return [_alert_to_response(a) for a in alerts]


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(db: DbDep) -> dict[str, Any]:
    """Get alert statistics.

    Args:
        db: Async database session (injected).

    Returns:
        Statistics including total, unacknowledged, and counts by type.
    """
    # Total count
    total_result = await db.execute(select(func.count(Alert.id)))
    total: int = total_result.scalar_one()

    # Unacknowledged count
    unack_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.acknowledged == False),  # noqa: E712
    )
    unacknowledged: int = unack_result.scalar_one()

    # Counts by type
    type_result = await db.execute(
        select(Alert.alert_type, func.count(Alert.id)).group_by(Alert.alert_type),
    )
    by_type: dict[str, int] = {row[0]: row[1] for row in type_result.all()}

    return {
        "total": total,
        "unacknowledged": unacknowledged,
        "by_type": by_type,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: DbDep) -> dict[str, Any]:
    """Get a single alert by ID.

    Args:
        alert_id: Alert ID to retrieve.
        db: Async database session (injected).

    Returns:
        Alert data.

    Raises:
        HTTPException: 404 if alert not found.
    """
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalars().first()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return _alert_to_response(alert)


@router.post("/test", response_model=TestAlertResponse)
async def send_test_alert(request: TestAlertRequest) -> dict[str, Any]:
    """Send a test alert via Telegram.

    Args:
        request: Test alert request with message.

    Returns:
        Success status and message.

    Raises:
        HTTPException: 503 if Telegram is not configured or fails.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise HTTPException(
            status_code=503,
            detail="Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.",
        )

    try:
        async with TelegramBot(
            token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        ) as bot:
            success = await bot.send_message(f"🧪 *Test Alert*\n\n{request.message}")

        if success:
            logger.info("test_alert_sent", message=request.message)
            return {"success": True, "message": "Test alert sent successfully"}
        else:
            logger.warning("test_alert_failed")
            raise HTTPException(status_code=503, detail="Failed to send test alert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("test_alert_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"Telegram error: {e}") from e


@router.put("/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_alert(alert_id: int, db: DbDep) -> dict[str, Any]:
    """Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge.
        db: Async database session (injected).

    Returns:
        Acknowledgement confirmation.

    Raises:
        HTTPException: 404 if alert not found.
    """
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalars().first()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    now = datetime.now(UTC)
    alert.acknowledged = True
    alert.acknowledged_at = now
    await db.commit()

    logger.info("alert_acknowledged", alert_id=alert_id)
    return {
        "id": alert_id,
        "acknowledged": True,
        "acknowledged_at": now.isoformat(),
    }
