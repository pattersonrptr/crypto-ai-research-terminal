"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import (
    alerts,
    backtesting,
    graph,
    narratives,
    rankings,
    reports,
    scheduler,
    tokens,
)

app = FastAPI(
    title="Crypto AI Research Terminal",
    description="Personal AI-powered cryptocurrency market intelligence platform.",
    version="0.1.0",
)

app.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
app.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
app.include_router(narratives.router, prefix="/narratives", tags=["narratives"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(backtesting.router, prefix="/backtesting", tags=["backtesting"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
