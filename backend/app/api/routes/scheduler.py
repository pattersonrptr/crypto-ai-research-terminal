"""Scheduler status route handlers.

Provides endpoints for viewing scheduler job health:
- GET /scheduler/status       — Status of the primary daily_collection_job
- GET /scheduler/status/all   — Status of all registered jobs
"""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger(__name__)

# Registered job names — extend as new jobs are added
_REGISTERED_JOBS: list[str] = ["daily_collection_job"]


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------


class JobStatusResponse(BaseModel):
    """Scheduler job health status response."""

    job_name: str
    last_run: str | None
    last_status: str | None
    error_count: int
    last_error: str | None


# ---------------------------------------------------------------------------
# Public helpers (patchable in tests)
# ---------------------------------------------------------------------------


async def get_job_status(job_name: str) -> dict[str, Any]:
    """Retrieve job status from Redis, falling back gracefully when unavailable.

    Args:
        job_name: Scheduler job identifier.

    Returns:
        Dict matching ``JobStatusResponse`` schema.
    """
    try:
        import redis.asyncio as aioredis  # noqa: PLC0415

        from app.config import settings  # noqa: PLC0415
        from app.scheduler.jobs import get_job_status as _get  # noqa: PLC0415

        client: aioredis.Redis[bytes] = aioredis.from_url(
            settings.redis_url, decode_responses=False
        )
        try:
            return await _get(redis=client, job_name=job_name)
        finally:
            await client.close()
    except Exception:
        logger.warning("scheduler.redis_unavailable", job=job_name)
        return {
            "job_name": job_name,
            "last_run": None,
            "last_status": None,
            "error_count": 0,
            "last_error": None,
        }


async def get_all_job_statuses() -> list[dict[str, Any]]:
    """Return status for all registered scheduler jobs."""
    return [await get_job_status(name) for name in _REGISTERED_JOBS]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", response_model=JobStatusResponse)
async def scheduler_status() -> dict[str, Any]:
    """Return health status of the primary daily_collection_job.

    Returns:
        JobStatusResponse with last_run, last_status, error_count,
        last_error. All fields are null when the job has never run.
    """
    result = await get_job_status("daily_collection_job")
    logger.info("scheduler.status.requested", status=result.get("last_status"))
    return result


@router.get("/status/all", response_model=list[JobStatusResponse])
async def scheduler_status_all() -> list[dict[str, Any]]:
    """Return health status for all registered scheduler jobs.

    Returns:
        List of JobStatusResponse objects.
    """
    results = await get_all_job_statuses()
    logger.info("scheduler.status_all.requested", count=len(results))
    return results
