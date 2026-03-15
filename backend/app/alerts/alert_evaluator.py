"""AlertEvaluator — bridges scored pipeline data to Alert ORM objects.

Takes the scored result dicts produced by the daily pipeline and runs
them through the :class:`AlertRuleEngine`.  For every triggered rule the
evaluator creates an :class:`Alert` ORM instance (not yet persisted).
"""

from __future__ import annotations

from typing import Any

import structlog

from app.alerts.alert_formatter import AlertType
from app.alerts.alert_rules import AlertRuleEngine
from app.models.alert import Alert

logger = structlog.get_logger(__name__)

# Mapping: pipeline data key → (rule data key, scale factor).
# Rules expect specific key names (e.g. "listing_score") while the pipeline
# uses different names (e.g. "listing_probability") and 0-1 ranges.
_PIPELINE_TO_RULE: list[tuple[str, str, float]] = [
    # (pipeline_key,       rule_key,           scale)
    ("listing_probability", "listing_score", 100.0),  # 0-1 → 0-100
    ("risk_score", "risk_score", 1.0),  # already 0-1
    ("whale_score", "whale_score", 10.0),  # 0-1 → 0-10
    ("confidence", "confidence", 1.0),
    ("unlock_pct", "unlock_pct", 1.0),
    ("momentum_score", "momentum_score", 10.0),  # 0-1 → 0-10
    ("social_growth_pct", "social_growth_pct", 1.0),
]

# Which pipeline key is relevant per alert type (for metadata extraction).
_ALERT_PIPELINE_KEY: dict[AlertType, str] = {
    AlertType.LISTING_CANDIDATE: "listing_probability",
    AlertType.RUGPULL_RISK: "risk_score",
    AlertType.WHALE_ACCUMULATION: "whale_score",
    AlertType.MANIPULATION_DETECTED: "confidence",
    AlertType.TOKEN_UNLOCK_SOON: "unlock_pct",
    AlertType.NARRATIVE_EMERGING: "momentum_score",
    AlertType.MEMECOIN_HYPE_DETECTED: "social_growth_pct",
}


def _build_rule_data(token_data: dict[str, Any]) -> dict[str, Any]:
    """Build the data dict that AlertRuleEngine.evaluate_all expects.

    Translates pipeline key names to rule key names and scales values.
    """
    rule_data: dict[str, Any] = {}
    for pipeline_key, rule_key, scale in _PIPELINE_TO_RULE:
        raw = float(token_data.get(pipeline_key, 0.0))
        rule_data[rule_key] = raw * scale
    return rule_data


def _build_message(alert_type: AlertType, token_data: dict[str, Any]) -> str:
    """Build a human-readable message for the alert."""
    symbol = token_data.get("symbol", "???")
    name = token_data.get("name", symbol)
    messages: dict[AlertType, str] = {
        AlertType.LISTING_CANDIDATE: (
            f"{name} ({symbol}) shows strong listing signals "
            f"(probability={token_data.get('listing_probability', 0):.0%})"
        ),
        AlertType.RUGPULL_RISK: (
            f"{name} ({symbol}) has elevated rug-pull risk "
            f"(risk_score={token_data.get('risk_score', 0):.2f})"
        ),
        AlertType.WHALE_ACCUMULATION: (f"Whale accumulation detected for {name} ({symbol})"),
        AlertType.MANIPULATION_DETECTED: (f"Potential manipulation detected for {name} ({symbol})"),
        AlertType.TOKEN_UNLOCK_SOON: (
            f"Significant token unlock approaching for {name} ({symbol})"
        ),
        AlertType.NARRATIVE_EMERGING: (f"{name} ({symbol}) is part of an emerging narrative"),
        AlertType.MEMECOIN_HYPE_DETECTED: (f"Memecoin hype detected for {name} ({symbol})"),
    }
    return messages.get(alert_type, f"Alert for {symbol}: {alert_type.value}")


def _extract_metadata(alert_type: AlertType, token_data: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant scores/data to store in alert_metadata."""
    meta: dict[str, Any] = {
        "opportunity_score": token_data.get("opportunity_score"),
        "fundamental_score": token_data.get("fundamental_score"),
    }
    key = _ALERT_PIPELINE_KEY.get(alert_type)
    if key and key in token_data:
        meta[key] = token_data[key]
    return meta


class AlertEvaluator:
    """Evaluate scored pipeline data and produce Alert ORM objects."""

    def __init__(self, engine: AlertRuleEngine | None = None) -> None:
        self._engine = engine or AlertRuleEngine.create_default()

    def evaluate(self, token_data: dict[str, Any]) -> list[Alert]:
        """Evaluate one token's pipeline data against all rules.

        Args:
            token_data: Scored pipeline dict (symbol, scores, etc.).

        Returns:
            List of Alert ORM objects for triggered rules (not persisted).
        """
        rule_data = _build_rule_data(token_data)
        triggered = self._engine.evaluate_all(rule_data)

        alerts: list[Alert] = []
        for hit in triggered:
            alert_type: AlertType = hit["alert_type"]
            alert = Alert(
                token_id=token_data.get("token_id"),
                token_symbol=str(token_data.get("symbol", "")),
                alert_type=alert_type.value,
                message=_build_message(alert_type, token_data),
                alert_metadata=_extract_metadata(alert_type, token_data),
            )
            alerts.append(alert)

        if alerts:
            logger.info(
                "alert_evaluator.triggered",
                symbol=token_data.get("symbol"),
                count=len(alerts),
                types=[a.alert_type for a in alerts],
            )
        return alerts

    def evaluate_batch(self, batch: list[dict[str, Any]]) -> list[Alert]:
        """Evaluate a batch of scored pipeline dicts.

        Args:
            batch: List of scored token dicts.

        Returns:
            Flat list of all triggered Alert objects.
        """
        all_alerts: list[Alert] = []
        for token_data in batch:
            all_alerts.extend(self.evaluate(token_data))
        return all_alerts
