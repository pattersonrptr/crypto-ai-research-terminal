"""AlertFormatter — formats alerts for Telegram delivery.

Supports multiple alert types defined in SCOPE.md section 6.10:
- LISTING_CANDIDATE
- WHALE_ACCUMULATION
- RUGPULL_RISK
- MANIPULATION_DETECTED
- TOKEN_UNLOCK_SOON
- NARRATIVE_EMERGING
- MEMECOIN_HYPE_DETECTED
- DAILY_REPORT
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


class AlertType(Enum):
    """Types of alerts supported by the system."""

    LISTING_CANDIDATE = "listing_candidate"
    WHALE_ACCUMULATION = "whale_accumulation"
    RUGPULL_RISK = "rugpull_risk"
    MANIPULATION_DETECTED = "manipulation_detected"
    TOKEN_UNLOCK_SOON = "token_unlock_soon"  # noqa: S105
    NARRATIVE_EMERGING = "narrative_emerging"
    MEMECOIN_HYPE_DETECTED = "memecoin_hype_detected"
    DAILY_REPORT = "daily_report"


# Emoji mapping for each alert type
ALERT_EMOJIS: dict[AlertType, str] = {
    AlertType.LISTING_CANDIDATE: "🚨",
    AlertType.WHALE_ACCUMULATION: "🐋",
    AlertType.RUGPULL_RISK: "⚠️",
    AlertType.MANIPULATION_DETECTED: "🔴",
    AlertType.TOKEN_UNLOCK_SOON: "🔓",
    AlertType.NARRATIVE_EMERGING: "📈",
    AlertType.MEMECOIN_HYPE_DETECTED: "🚀",
    AlertType.DAILY_REPORT: "📊",
}


@dataclass
class FormattedAlert:
    """A formatted alert ready for delivery."""

    title: str
    body: str
    emoji: str
    alert_type: AlertType

    def to_telegram(self) -> str:
        """Convert to Telegram message format with Markdown."""
        return f"{self.emoji} *{self.title}*\n\n{self.body}"


class AlertFormatter:
    """Formats alerts for Telegram delivery."""

    def format(self, alert_type: AlertType, data: dict[str, Any]) -> FormattedAlert:
        """Format an alert based on its type and data.

        Args:
            alert_type: The type of alert to format.
            data: Alert-specific data dictionary.

        Returns:
            FormattedAlert ready for delivery.

        Raises:
            ValueError: If alert_type is unknown.
            KeyError: If required data fields are missing.
        """
        if not isinstance(alert_type, AlertType):
            raise ValueError(f"Unknown alert type: {alert_type}")

        formatters = {
            AlertType.LISTING_CANDIDATE: self._format_listing_candidate,
            AlertType.WHALE_ACCUMULATION: self._format_whale_accumulation,
            AlertType.RUGPULL_RISK: self._format_rugpull_risk,
            AlertType.MANIPULATION_DETECTED: self._format_manipulation_detected,
            AlertType.TOKEN_UNLOCK_SOON: self._format_token_unlock,
            AlertType.NARRATIVE_EMERGING: self._format_narrative_emerging,
            AlertType.MEMECOIN_HYPE_DETECTED: self._format_memecoin_hype,
            AlertType.DAILY_REPORT: self._format_daily_report,
        }

        formatter_func = formatters.get(alert_type)
        if formatter_func is None:
            raise ValueError(f"Unknown alert type: {alert_type}")

        return formatter_func(data)

    def _format_listing_candidate(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a listing candidate alert."""
        # Required fields
        symbol = data["symbol"]
        name = data["name"]
        listing_score = data["listing_score"]
        signals = data["signals"]
        probability = data["probability"]
        likely_exchanges = data["likely_exchanges"]

        # Build signals list
        signals_text = ""
        if signals:
            signals_list = "\n".join(f"✅ {s}" for s in signals)
            signals_text = f"\n*Detected signals:*\n{signals_list}\n"

        # Build exchanges text
        exchanges_text = ""
        if likely_exchanges:
            exchanges_text = f"\n*Most likely exchanges:* {', '.join(likely_exchanges)}"

        body = (
            f"*Token:* {name}\n"
            f"*Symbol:* {symbol}\n\n"
            f"*Listing score:* {listing_score}/100\n"
            f"{signals_text}"
            f"*Estimated probability:* {probability.capitalize()}"
            f"{exchanges_text}\n\n"
            f"⚠️ _Not a guarantee. DYOR._"
        )

        return FormattedAlert(
            title="LISTING CANDIDATE DETECTED",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.LISTING_CANDIDATE],
            alert_type=AlertType.LISTING_CANDIDATE,
        )

    def _format_whale_accumulation(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a whale accumulation alert."""
        symbol = data["symbol"]
        name = data["name"]
        whale_score = data["whale_score"]
        top10_change_pct = data["top10_change_pct"]
        large_transactions = data["large_transactions"]
        period_days = data["period_days"]

        body = (
            f"*Token:* {name} ({symbol})\n\n"
            f"*Whale activity score:* {whale_score:.1f}/10\n"
            f"*Top 10 wallets change:* {top10_change_pct:+.1f}%\n"
            f"*Large transactions:* {large_transactions} in {period_days} days\n\n"
            f"_Large wallets are accumulating this token._"
        )

        return FormattedAlert(
            title="WHALE ACCUMULATION DETECTED",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.WHALE_ACCUMULATION],
            alert_type=AlertType.WHALE_ACCUMULATION,
        )

    def _format_rugpull_risk(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a rugpull risk alert."""
        symbol = data["symbol"]
        name = data["name"]
        risk_score = data["risk_score"]
        risk_factors = data["risk_factors"]

        risk_pct = int(risk_score * 100)
        factors_text = "\n".join(f"🚩 {f}" for f in risk_factors)

        body = (
            f"*Token:* {name} ({symbol})\n\n"
            f"*Risk score:* {risk_pct}%\n\n"
            f"*Risk factors:*\n{factors_text}\n\n"
            f"⚠️ _Exercise extreme caution with this token._"
        )

        return FormattedAlert(
            title="RUGPULL RISK ALERT",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.RUGPULL_RISK],
            alert_type=AlertType.RUGPULL_RISK,
        )

    def _format_manipulation_detected(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a manipulation detected alert."""
        symbol = data["symbol"]
        name = data["name"]
        manipulation_type = data["manipulation_type"]
        confidence = data["confidence"]
        indicators = data["indicators"]

        type_display = manipulation_type.replace("_", " ").title()
        confidence_pct = int(confidence * 100)
        indicators_text = "\n".join(f"• {i}" for i in indicators)

        body = (
            f"*Token:* {name} ({symbol})\n\n"
            f"*Type:* {type_display}\n"
            f"*Confidence:* {confidence_pct}%\n\n"
            f"*Indicators:*\n{indicators_text}\n\n"
            f"⚠️ _Potential market manipulation detected._"
        )

        return FormattedAlert(
            title="MANIPULATION DETECTED",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.MANIPULATION_DETECTED],
            alert_type=AlertType.MANIPULATION_DETECTED,
        )

    def _format_token_unlock(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a token unlock alert."""
        symbol = data["symbol"]
        name = data["name"]
        unlock_pct = data["unlock_pct"]
        unlock_date: datetime = data["unlock_date"]
        unlock_usd_value = data["unlock_usd_value"]

        date_str = unlock_date.strftime("%Y-%m-%d")
        value_str = f"${unlock_usd_value:,.0f}"

        body = (
            f"*Token:* {name} ({symbol})\n\n"
            f"*Unlock amount:* {unlock_pct:.1f}% of supply\n"
            f"*Unlock date:* {date_str}\n"
            f"*Estimated value:* {value_str}\n\n"
            f"_Large unlock may create selling pressure._"
        )

        return FormattedAlert(
            title="TOKEN UNLOCK APPROACHING",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.TOKEN_UNLOCK_SOON],
            alert_type=AlertType.TOKEN_UNLOCK_SOON,
        )

    def _format_narrative_emerging(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a narrative emerging alert."""
        narrative = data["narrative"]
        momentum_score = data["momentum_score"]
        top_tokens = data["top_tokens"]
        mention_growth_pct = data["mention_growth_pct"]

        tokens_text = ", ".join(top_tokens[:5])

        body = (
            f"*Narrative:* {narrative}\n\n"
            f"*Momentum score:* {momentum_score:.1f}/10\n"
            f"*Mention growth:* +{mention_growth_pct}%\n\n"
            f"*Top tokens:* {tokens_text}\n\n"
            f"_This narrative is gaining traction._"
        )

        return FormattedAlert(
            title="EMERGING NARRATIVE DETECTED",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.NARRATIVE_EMERGING],
            alert_type=AlertType.NARRATIVE_EMERGING,
        )

    def _format_memecoin_hype(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a memecoin hype alert."""
        symbol = data["symbol"]
        name = data["name"]
        social_growth_pct = data["social_growth_pct"]
        volume_growth_pct = data["volume_growth_pct"]
        holder_growth_pct = data["holder_growth_pct"]

        body = (
            f"*Token:* {name} ({symbol})\n\n"
            f"*Social growth:* +{social_growth_pct}%\n"
            f"*Volume growth:* +{volume_growth_pct}%\n"
            f"*Holder growth:* +{holder_growth_pct}%\n\n"
            f"⚠️ _High volatility expected. Extreme caution advised._"
        )

        return FormattedAlert(
            title="MEMECOIN HYPE DETECTED",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.MEMECOIN_HYPE_DETECTED],
            alert_type=AlertType.MEMECOIN_HYPE_DETECTED,
        )

    def _format_daily_report(self, data: dict[str, Any]) -> FormattedAlert:
        """Format a daily report alert."""
        date: datetime = data["date"]
        top_opportunities = data["top_opportunities"]
        active_alerts_count = data["active_alerts_count"]
        market_sentiment = data["market_sentiment"]

        date_str = date.strftime("%Y-%m-%d")

        # Build top opportunities list
        opportunities_text = ""
        for i, opp in enumerate(top_opportunities[:5], 1):
            score_pct = int(opp["score"] * 100)
            opportunities_text += f"{i}. {opp['symbol']} — {score_pct}%\n"

        sentiment_emoji = (
            "🟢"
            if market_sentiment == "bullish"
            else "🔴"
            if market_sentiment == "bearish"
            else "🟡"
        )

        body = (
            f"*Date:* {date_str}\n"
            f"*Market sentiment:* {sentiment_emoji} {market_sentiment.capitalize()}\n\n"
            f"*Top opportunities:*\n{opportunities_text}\n"
            f"*Active alerts:* {active_alerts_count}\n\n"
            f"_Check the dashboard for full details._"
        )

        return FormattedAlert(
            title="DAILY MARKET REPORT",
            body=body,
            emoji=ALERT_EMOJIS[AlertType.DAILY_REPORT],
            alert_type=AlertType.DAILY_REPORT,
        )
