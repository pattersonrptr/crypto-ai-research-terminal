"""ScoreExplainer — generates human-readable explanations for scoring pillars.

Produces 1-2 sentence explanations per pillar based on the actual data
that drove the score, helping users understand *why* a token scored high
or low on each dimension.

Usage::

    explanations = ScoreExplainer.explain(token_data)
    for p in explanations:
        print(f"{p.pillar}: {p.score:.0%} — {p.explanation}")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _rating(score: float) -> str:
    """Return a human-readable rating word for a [0, 1] score."""
    if score >= 0.80:
        return "very strong"
    if score >= 0.60:
        return "strong"
    if score >= 0.40:
        return "moderate"
    if score >= 0.20:
        return "weak"
    return "very weak"


def _fmt(value: float | int, fmt: str = ",.0f") -> str:
    """Format a number with commas (safe for None)."""
    return format(value, fmt)


@dataclass(frozen=True, slots=True)
class PillarExplanation:
    """Immutable explanation for a single scoring pillar."""

    pillar: str
    score: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict."""
        return {
            "pillar": self.pillar,
            "score": self.score,
            "explanation": self.explanation,
        }


class ScoreExplainer:
    """Generates per-pillar explanations from token scoring data."""

    @staticmethod
    def explain(token_data: dict[str, Any]) -> list[PillarExplanation]:
        """Generate explanations for all 5 pillars + overall summary.

        Args:
            token_data: Dict containing score fields (``fundamental_score``,
                ``technology_score``, etc.) and optional market/social fields.

        Returns:
            List of 6 :class:`PillarExplanation` objects (5 pillars + overall).
        """
        return [
            ScoreExplainer._explain_fundamental(token_data),
            ScoreExplainer._explain_growth(token_data),
            ScoreExplainer._explain_narrative(token_data),
            ScoreExplainer._explain_listing(token_data),
            ScoreExplainer._explain_risk(token_data),
            ScoreExplainer._explain_overall(token_data),
        ]

    # ------------------------------------------------------------------
    # Private pillar explainers
    # ------------------------------------------------------------------

    @staticmethod
    def _explain_fundamental(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("fundamental_score", 0.0))
        tech = float(data.get("technology_score", 0.0))
        tok = float(data.get("tokenomics_score", 0.0))
        adopt = float(data.get("adoption_score", 0.0))
        dev = float(data.get("dev_activity_score", 0.0))

        # Find strongest and weakest sub-pillars
        subs = {
            "technology": tech,
            "tokenomics": tok,
            "adoption": adopt,
            "dev activity": dev,
        }
        best = max(subs, key=subs.get)  # type: ignore[arg-type]
        worst = min(subs, key=subs.get)  # type: ignore[arg-type]

        parts: list[str] = [
            f"Fundamental score is {_rating(score)} ({score:.0%}).",
        ]
        if subs[best] > 0:
            parts.append(f"Strongest sub-pillar: {best} ({subs[best]:.0%}).")
        if subs[worst] < subs[best]:
            parts.append(f"Weakest: {worst} ({subs[worst]:.0%}).")
        return PillarExplanation(
            pillar="fundamental",
            score=score,
            explanation=" ".join(parts),
        )

    @staticmethod
    def _explain_growth(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("growth_score", 0.0))
        volume = data.get("volume_24h_usd")
        price_chg = data.get("price_change_7d")

        parts: list[str] = [
            f"Growth/momentum score is {_rating(score)} ({score:.0%}).",
        ]
        if price_chg is not None:
            direction = "up" if price_chg > 0 else "down"
            parts.append(f"Price {direction} {abs(price_chg):.1f}% over 7 days.")
        if volume is not None and volume > 0:
            parts.append(f"24h volume: ${_fmt(volume)}.")
        return PillarExplanation(
            pillar="growth",
            score=score,
            explanation=" ".join(parts),
        )

    @staticmethod
    def _explain_narrative(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("narrative_score", 0.0))
        reddit_subs = data.get("reddit_subscribers", 0) or 0
        twitter_mentions = data.get("twitter_mentions_24h", 0) or 0
        sentiment = data.get("sentiment_score", 0.0) or 0.0

        parts: list[str] = [
            f"Narrative/social score is {_rating(score)} ({score:.0%}).",
        ]
        if reddit_subs > 0:
            parts.append(f"Reddit community: {_fmt(reddit_subs)} subscribers.")
        if twitter_mentions > 0:
            parts.append(f"Twitter: {_fmt(twitter_mentions)} mentions in 24h.")
        if sentiment > 0:
            sent_label = "positive" if sentiment >= 0.6 else "neutral"
            parts.append(f"Sentiment: {sent_label} ({sentiment:.0%}).")
        return PillarExplanation(
            pillar="narrative",
            score=score,
            explanation=" ".join(parts),
        )

    @staticmethod
    def _explain_listing(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("listing_probability", 0.0))
        market_cap = data.get("market_cap_usd")

        parts: list[str] = [
            f"Listing probability is {_rating(score)} ({score:.0%}).",
        ]
        if score >= 0.60:
            parts.append("Strong candidate for new exchange listings.")
        elif score >= 0.30:
            parts.append("Moderate listing potential.")
        else:
            parts.append("Low listing probability at this time.")
        if market_cap is not None and market_cap > 0:
            parts.append(f"Market cap: ${_fmt(market_cap)}.")
        return PillarExplanation(
            pillar="listing",
            score=score,
            explanation=" ".join(parts),
        )

    @staticmethod
    def _explain_risk(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("risk_score", 0.0))

        if score >= 0.70:
            text = (
                f"Risk-adjusted score is {_rating(score)} ({score:.0%}). "
                "Low risk profile — fundamentals suggest solid backing."
            )
        elif score >= 0.40:
            text = (
                f"Risk-adjusted score is {_rating(score)} ({score:.0%}). "
                "Moderate risk — some caution advised."
            )
        else:
            text = (
                f"Risk-adjusted score is {_rating(score)} ({score:.0%}). "
                "Elevated risk — exercise significant caution."
            )
        return PillarExplanation(
            pillar="risk",
            score=score,
            explanation=text,
        )

    @staticmethod
    def _explain_overall(data: dict[str, Any]) -> PillarExplanation:
        score = float(data.get("opportunity_score", 0.0))
        symbol = data.get("symbol", "?")

        if score >= 0.70:
            text = (
                f"{symbol} has a {_rating(score)} overall opportunity score "
                f"({score:.0%}). This token shows strong potential across "
                "multiple dimensions."
            )
        elif score >= 0.40:
            text = (
                f"{symbol} has a {_rating(score)} overall opportunity score "
                f"({score:.0%}). Solid but with room for improvement in "
                "some areas."
            )
        else:
            text = (
                f"{symbol} has a {_rating(score)} overall opportunity score "
                f"({score:.0%}). Limited opportunity signal at this time."
            )
        return PillarExplanation(
            pillar="overall",
            score=score,
            explanation=text,
        )
