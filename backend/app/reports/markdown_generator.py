"""MarkdownGenerator — renders Markdown reports using Jinja2 templates.

Generates token reports and market reports from data dictionaries.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Default template path
DEFAULT_TEMPLATE_PATH = Path(__file__).parent / "templates"


def format_large_number(value: float) -> str:
    """Format large numbers with abbreviations.

    Args:
        value: Number to format.

    Returns:
        Formatted string with abbreviations (K, M, B, T).
    """
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.2f}"


def get_listing_assessment(score: int) -> str:
    """Get human-readable assessment for listing score.

    Args:
        score: Listing score (0-100).

    Returns:
        Assessment string.
    """
    if score >= 80:
        return "🔥 Very High Potential"
    if score >= 60:
        return "✅ High Potential"
    if score >= 40:
        return "🟡 Moderate Potential"
    if score >= 20:
        return "⚪ Low Potential"
    return "⬜ Already Listed / No Signal"


def get_risk_assessment(score: float) -> str:
    """Get human-readable assessment for risk score.

    Args:
        score: Risk score (0-1).

    Returns:
        Assessment string.
    """
    if score >= 0.8:
        return "🔴 Critical Risk"
    if score >= 0.6:
        return "🟠 High Risk"
    if score >= 0.4:
        return "🟡 Moderate Risk"
    if score >= 0.2:
        return "🟢 Low Risk"
    return "✅ Very Low Risk"


def get_whale_assessment(score: float) -> str:
    """Get human-readable assessment for whale score.

    Args:
        score: Whale activity score (0-10).

    Returns:
        Assessment string.
    """
    if score >= 8:
        return "🐋 Very High Activity"
    if score >= 6:
        return "🐳 High Activity"
    if score >= 4:
        return "🐟 Moderate Activity"
    return "🦐 Low Activity"


def get_sentiment_emoji(sentiment: str) -> str:
    """Get emoji for market sentiment.

    Args:
        sentiment: Sentiment string (bullish, bearish, neutral).

    Returns:
        Emoji string.
    """
    sentiment_emojis = {
        "bullish": "🟢",
        "bearish": "🔴",
        "neutral": "🟡",
    }
    return sentiment_emojis.get(sentiment.lower(), "⚪")


class MarkdownGenerator:
    """Generates Markdown reports using Jinja2 templates."""

    def __init__(self, template_path: Path | None = None) -> None:
        """Initialize the generator with Jinja2 environment.

        Args:
            template_path: Optional custom path to templates directory.
        """
        path = template_path or DEFAULT_TEMPLATE_PATH
        self._env = Environment(
            loader=FileSystemLoader(path),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters/globals
        self._env.globals["format_large_number"] = format_large_number
        self._env.globals["get_listing_assessment"] = get_listing_assessment
        self._env.globals["get_risk_assessment"] = get_risk_assessment
        self._env.globals["get_whale_assessment"] = get_whale_assessment
        self._env.globals["get_sentiment_emoji"] = get_sentiment_emoji

    @property
    def env(self) -> Environment:
        """Return the Jinja2 environment."""
        return self._env

    def generate_token_report(self, data: dict[str, Any]) -> str:
        """Generate a token report from data.

        Args:
            data: Dictionary containing token data:
                - symbol: Token symbol
                - name: Token name
                - price_usd: Current price in USD
                - market_cap_usd: Market capitalization
                - volume_24h_usd: 24-hour trading volume
                - listing_score: Listing potential score (0-100)
                - risk_score: Risk score (0-1)
                - whale_score: Whale activity score (0-10)
                - signals: Optional list of detected signals
                - risk_factors: Optional list of risk factors
                - generated_at: Report generation timestamp

        Returns:
            Rendered Markdown string.
        """
        # Ensure optional fields have defaults
        data.setdefault("signals", [])
        data.setdefault("risk_factors", [])

        template = self._env.get_template("token_report.md.j2")
        return template.render(**data)

    def generate_market_report(self, data: dict[str, Any]) -> str:
        """Generate a daily market report from data.

        Args:
            data: Dictionary containing market data:
                - date: Report date
                - market_sentiment: bullish/bearish/neutral
                - total_market_cap_usd: Total crypto market cap
                - btc_dominance_pct: Bitcoin dominance percentage
                - top_opportunities: List of top tokens with scores
                - active_alerts_count: Number of active alerts
                - emerging_narratives: List of emerging narrative names

        Returns:
            Rendered Markdown string.
        """
        template = self._env.get_template("market_report.md.j2")
        return template.render(**data)
