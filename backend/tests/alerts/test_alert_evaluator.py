"""Tests for AlertEvaluator — Phase 11.

The AlertEvaluator takes scored pipeline dicts, runs them through the
AlertRuleEngine, and returns Alert ORM objects ready for persistence.
"""

from __future__ import annotations

from typing import Any

from app.alerts.alert_evaluator import AlertEvaluator
from app.alerts.alert_formatter import AlertType
from app.models.alert import Alert


def _make_token_data(
    *,
    symbol: str = "XYZ",
    name: str = "Xyz Coin",
    token_id: int | None = 42,
    listing_probability: float = 0.0,
    risk_score: float = 0.0,
    growth_score: float = 0.0,
    narrative_score: float = 0.0,
    **overrides: Any,
) -> dict[str, Any]:
    """Create minimal scored pipeline data dict for testing."""
    return {
        "symbol": symbol,
        "name": name,
        "token_id": token_id,
        "listing_probability": listing_probability,
        "risk_score": risk_score,
        "growth_score": growth_score,
        "narrative_score": narrative_score,
        "opportunity_score": 0.5,
        "fundamental_score": 0.5,
        "price_usd": 1.0,
        "market_cap_usd": 1_000_000,
        "volume_24h_usd": 100_000,
        **overrides,
    }


class TestAlertEvaluator:
    """AlertEvaluator translates pipeline data into Alert ORM objects."""

    def test_no_alerts_when_all_scores_low(self) -> None:
        """Nothing triggers when scores are all below threshold."""
        evaluator = AlertEvaluator()
        data = _make_token_data()
        alerts = evaluator.evaluate(data)
        assert alerts == []

    def test_listing_candidate_triggers(self) -> None:
        """High listing_probability triggers a LISTING_CANDIDATE alert."""
        evaluator = AlertEvaluator()
        data = _make_token_data(listing_probability=0.85)
        alerts = evaluator.evaluate(data)

        assert len(alerts) == 1
        alert = alerts[0]
        assert isinstance(alert, Alert)
        assert alert.alert_type == AlertType.LISTING_CANDIDATE.value
        assert alert.token_symbol == "XYZ"
        assert "XYZ" in alert.message

    def test_rugpull_risk_triggers(self) -> None:
        """High risk_score triggers a RUGPULL_RISK alert."""
        evaluator = AlertEvaluator()
        data = _make_token_data(risk_score=0.75)
        alerts = evaluator.evaluate(data)

        types = [a.alert_type for a in alerts]
        assert AlertType.RUGPULL_RISK.value in types

    def test_multiple_rules_can_trigger(self) -> None:
        """If multiple thresholds exceeded, multiple alerts are generated."""
        evaluator = AlertEvaluator()
        data = _make_token_data(listing_probability=0.90, risk_score=0.80)
        alerts = evaluator.evaluate(data)

        types = {a.alert_type for a in alerts}
        assert AlertType.LISTING_CANDIDATE.value in types
        assert AlertType.RUGPULL_RISK.value in types

    def test_alert_metadata_contains_scores(self) -> None:
        """Generated alerts include relevant scores in alert_metadata."""
        evaluator = AlertEvaluator()
        data = _make_token_data(listing_probability=0.90)
        alerts = evaluator.evaluate(data)

        alert = alerts[0]
        assert alert.alert_metadata is not None
        assert "listing_probability" in alert.alert_metadata

    def test_evaluate_batch(self) -> None:
        """evaluate_batch processes multiple tokens and returns flat list."""
        evaluator = AlertEvaluator()
        batch = [
            _make_token_data(symbol="AAA", listing_probability=0.90),
            _make_token_data(symbol="BBB"),  # no triggers
            _make_token_data(symbol="CCC", risk_score=0.70),
        ]
        alerts = evaluator.evaluate_batch(batch)
        symbols = {a.token_symbol for a in alerts}
        assert "AAA" in symbols
        assert "BBB" not in symbols
        assert "CCC" in symbols

    def test_token_id_propagated(self) -> None:
        """Alert inherits token_id from pipeline data when present."""
        evaluator = AlertEvaluator()
        data = _make_token_data(token_id=99, listing_probability=0.90)
        alerts = evaluator.evaluate(data)
        assert alerts[0].token_id == 99

    def test_token_id_none_when_missing(self) -> None:
        """Alert gets token_id=None when pipeline data lacks it."""
        evaluator = AlertEvaluator()
        data = _make_token_data(token_id=None, listing_probability=0.90)
        alerts = evaluator.evaluate(data)
        assert alerts[0].token_id is None
