"""Alerts route handlers.

Provides endpoints for managing and viewing alerts:
- GET /alerts - List all alerts with filtering
- GET /alerts/stats - Get alert statistics
- GET /alerts/{id} - Get single alert
- POST /alerts/test - Send test alert
- PUT /alerts/{id}/acknowledge - Acknowledge alert
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.alerts.alert_formatter import AlertType
from app.alerts.telegram_bot import TelegramBot
from app.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

# In-memory storage for demo (replace with DB in production)
_alerts_store: list[dict[str, Any]] = []
_alert_id_counter = 0


def _get_next_id() -> int:
    """Get next alert ID."""
    global _alert_id_counter
    _alert_id_counter += 1
    return _alert_id_counter


# --- Pydantic models ---


class AlertResponse(BaseModel):
    """Alert response schema."""

    id: int
    alert_type: str
    message: str
    triggered_at: datetime
    acknowledged: bool = False
    token_symbol: str | None = None


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
    acknowledged_at: datetime


# --- Route handlers ---


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=200, description="Max alerts to return"),
    alert_type: str | None = Query(default=None, description="Filter by alert type"),
    acknowledged: bool | None = Query(default=None, description="Filter by ack status"),
) -> list[dict[str, Any]]:
    """Get list of alerts with optional filtering.

    Args:
        limit: Maximum number of alerts to return.
        alert_type: Optional filter by alert type.
        acknowledged: Optional filter by acknowledged status.

    Returns:
        List of alerts matching the criteria.
    """
    filtered = _alerts_store.copy()

    if alert_type:
        filtered = [a for a in filtered if a["alert_type"] == alert_type]

    if acknowledged is not None:
        filtered = [a for a in filtered if a["acknowledged"] == acknowledged]

    # Sort by triggered_at descending (newest first)
    filtered.sort(key=lambda x: x["triggered_at"], reverse=True)

    return filtered[:limit]


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats() -> dict[str, Any]:
    """Get alert statistics.

    Returns:
        Statistics including total, unacknowledged, and counts by type.
    """
    total = len(_alerts_store)
    unacknowledged = sum(1 for a in _alerts_store if not a["acknowledged"])

    by_type: dict[str, int] = {}
    for alert in _alerts_store:
        atype = alert["alert_type"]
        by_type[atype] = by_type.get(atype, 0) + 1

    return {
        "total": total,
        "unacknowledged": unacknowledged,
        "by_type": by_type,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int) -> dict[str, Any]:
    """Get a single alert by ID.

    Args:
        alert_id: Alert ID to retrieve.

    Returns:
        Alert data.

    Raises:
        HTTPException: 404 if alert not found.
    """
    for alert in _alerts_store:
        if alert["id"] == alert_id:
            return alert

    raise HTTPException(status_code=404, detail="Alert not found")


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
    # Check if Telegram is configured
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
async def acknowledge_alert(alert_id: int) -> dict[str, Any]:
    """Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge.

    Returns:
        Acknowledgement confirmation.

    Raises:
        HTTPException: 404 if alert not found.
    """
    for alert in _alerts_store:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.now(UTC)
            logger.info("alert_acknowledged", alert_id=alert_id)
            return {
                "id": alert_id,
                "acknowledged": True,
                "acknowledged_at": alert["acknowledged_at"],
            }

    raise HTTPException(status_code=404, detail="Alert not found")


# --- Helper functions for creating alerts (used by other modules) ---


def create_alert(
    alert_type: AlertType,
    message: str,
    token_symbol: str | None = None,
) -> dict[str, Any]:
    """Create a new alert and store it.

    Args:
        alert_type: Type of alert.
        message: Alert message.
        token_symbol: Optional token symbol.

    Returns:
        Created alert data.
    """
    alert = {
        "id": _get_next_id(),
        "alert_type": alert_type.value,
        "message": message,
        "triggered_at": datetime.now(UTC),
        "acknowledged": False,
        "token_symbol": token_symbol,
    }
    _alerts_store.append(alert)
    logger.info("alert_created", alert_id=alert["id"], alert_type=alert_type.value)
    return alert


def clear_alerts() -> None:
    """Clear all alerts (for testing)."""
    global _alert_id_counter
    _alerts_store.clear()
    _alert_id_counter = 0
