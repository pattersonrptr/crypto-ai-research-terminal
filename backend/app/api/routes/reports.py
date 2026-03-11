"""Reports route handlers."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def placeholder() -> dict[str, str]:
    """Placeholder endpoint — to be implemented."""
    return {"status": "not implemented"}
