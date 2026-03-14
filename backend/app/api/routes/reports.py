"""Reports route handlers.

Provides endpoints for generating token and market reports in various formats.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.reports.markdown_generator import MarkdownGenerator
from app.reports.pdf_generator import PDFGenerator

router = APIRouter()


class ReportFormat(str, Enum):
    """Supported report formats."""

    markdown = "markdown"
    pdf = "pdf"


# Type alias for format query parameter
FormatQuery = Annotated[ReportFormat, Query()]

# Initialize generators
_md_generator = MarkdownGenerator()
_pdf_generator = PDFGenerator()


def _get_mock_token_data(symbol: str) -> dict[str, Any]:
    """Get mock token data for demo purposes.

    In production, this would fetch from database/collectors.
    """
    return {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Token",
        "price_usd": 145.50,
        "market_cap_usd": 65000000000.0,
        "volume_24h_usd": 2500000000.0,
        "listing_score": 85,
        "risk_score": 0.25,
        "whale_score": 7.8,
        "signals": ["High volume", "Strong momentum", "Positive sentiment"],
        "risk_factors": ["Market volatility", "Regulatory uncertainty"],
        "generated_at": datetime.now(UTC),
    }


def _get_mock_market_data() -> dict[str, Any]:
    """Get mock market data for demo purposes.

    In production, this would fetch from database/collectors.
    """
    return {
        "date": datetime.now(UTC),
        "market_sentiment": "bullish",
        "total_market_cap_usd": 2500000000000.0,
        "btc_dominance_pct": 52.3,
        "top_opportunities": [
            {"name": "Solana", "symbol": "SOL", "score": 0.85},
            {"name": "Avalanche", "symbol": "AVAX", "score": 0.78},
            {"name": "Chainlink", "symbol": "LINK", "score": 0.75},
        ],
        "active_alerts_count": 5,
        "emerging_narratives": ["AI Tokens", "RWA", "DePIN"],
    }


@router.get("/token/{symbol}")
async def get_token_report(
    symbol: str,
    format: FormatQuery = ReportFormat.markdown,
) -> Response:
    """Generate token analysis report.

    Args:
        symbol: Token symbol (e.g., SOL, BTC, ETH)
        format: Output format (markdown or pdf)

    Returns:
        Report content in requested format
    """
    token_data = _get_mock_token_data(symbol)
    markdown_content = _md_generator.generate_token_report(token_data)

    if format == ReportFormat.pdf:
        pdf_bytes = _pdf_generator.generate_from_markdown(markdown_content)
        filename = f"{symbol.upper()}_report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default: markdown
    filename = f"{symbol.upper()}_report.md"
    return Response(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/market")
async def get_market_report(
    format: FormatQuery = ReportFormat.markdown,
) -> Response:
    """Generate daily market report.

    Args:
        format: Output format (markdown or pdf)

    Returns:
        Report content in requested format
    """
    market_data = _get_mock_market_data()
    markdown_content = _md_generator.generate_market_report(market_data)

    if format == ReportFormat.pdf:
        pdf_bytes = _pdf_generator.generate_from_markdown(markdown_content)
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        filename = f"market_report_{date_str}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default: markdown
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    filename = f"market_report_{date_str}.md"
    return Response(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
