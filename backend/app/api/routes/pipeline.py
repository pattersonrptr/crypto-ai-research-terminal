"""Pipeline collect-now route handlers.

Provides endpoints for on-demand data collection:

- POST /pipeline/collect-now       — Trigger an asynchronous collection job.
- GET  /pipeline/status/{job_id}   — Query the status of a running job.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# In-memory job registry (lightweight; replaced by Redis in production later)
# ---------------------------------------------------------------------------

_job_registry: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CollectNowResponse(BaseModel):
    """Response returned after triggering a collection job."""

    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Status of a collection job."""

    job_id: str
    status: str
    detail: str


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------


def _run_job_in_background(job_id: str) -> None:
    """Spawn an async background task for the collection job.

    This is extracted so tests can easily patch it without triggering real
    collection work.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(_execute_collection(job_id))


async def _execute_collection(job_id: str) -> None:
    """Run the full collection pipeline and update the job registry."""
    _job_registry[job_id]["status"] = "running"
    logger.info("collect_now.started", job_id=job_id)
    try:
        from app.scheduler.jobs import daily_collection_job  # noqa: PLC0415

        await daily_collection_job()
        _job_registry[job_id]["status"] = "completed"
        _job_registry[job_id]["detail"] = "collection finished"
        logger.info("collect_now.completed", job_id=job_id)
    except Exception:
        _job_registry[job_id]["status"] = "failed"
        _job_registry[job_id]["detail"] = "collection error"
        logger.exception("collect_now.failed", job_id=job_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/collect-now", status_code=202, response_model=CollectNowResponse)
async def collect_now() -> CollectNowResponse:
    """Trigger an asynchronous on-demand collection job.

    Returns a ``job_id`` that can be used to poll status via
    ``GET /pipeline/status/{job_id}``.
    """
    job_id = str(uuid.uuid4())
    _job_registry[job_id] = {"status": "pending", "detail": ""}
    _run_job_in_background(job_id)
    logger.info("collect_now.accepted", job_id=job_id)
    return CollectNowResponse(job_id=job_id, status="pending")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    """Query the status of a collection job.

    Raises ``404`` if the *job_id* is unknown.
    """
    entry = _job_registry.get(job_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=entry["status"],
        detail=entry.get("detail", ""),
    )
