"""FastAPI application entry point."""

import os

from fastapi import FastAPI

from app.api.routes import (
    alerts,
    backtesting,
    graph,
    market,
    narratives,
    rankings,
    reports,
    scheduler,
    summaries,
    tokens,
)
from app.logging_config import configure_logging

# Configure structured logging before anything else
configure_logging(
    json_output=os.getenv("LOG_FORMAT", "console") == "json",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)

app = FastAPI(
    title="Crypto AI Research Terminal",
    description="Personal AI-powered cryptocurrency market intelligence platform.",
    version="0.1.0",
)

app.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
app.include_router(summaries.router, prefix="/tokens", tags=["summaries"])
app.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
app.include_router(narratives.router, prefix="/narratives", tags=["narratives"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(backtesting.router, prefix="/backtesting", tags=["backtesting"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
