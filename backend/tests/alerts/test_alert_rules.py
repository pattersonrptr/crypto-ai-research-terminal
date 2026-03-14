"""Tests for AlertRules — defines trigger conditions for alerts.

TDD RED phase: Tests written before implementation.
"""

from datetime import datetime

from app.alerts.alert_formatter import AlertType
from app.alerts.alert_rules import (
    AlertRuleEngine,
    ListingCandidateRule,
    ManipulationDetectedRule,
    MemecoinHypeRule,
    NarrativeEmergingRule,
    RugpullRiskRule,
    TokenUnlockRule,
    WhaleAccumulationRule,
)


class TestAlertRule:
    """Test the base AlertRule protocol/interface."""

    def test_alert_rule_has_evaluate_method(self) -> None:
        """AlertRule subclasses must have evaluate method."""
        rule = ListingCandidateRule()
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

    def test_alert_rule_has_alert_type_property(self) -> None:
        """AlertRule subclasses must have alert_type property."""
        rule = ListingCandidateRule()
        assert hasattr(rule, "alert_type")
        assert isinstance(rule.alert_type, AlertType)


class TestListingCandidateRule:
    """Test ListingCandidateRule trigger conditions."""

    def test_listing_candidate_rule_alert_type(self) -> None:
        """ListingCandidateRule has correct alert type."""
        rule = ListingCandidateRule()
        assert rule.alert_type == AlertType.LISTING_CANDIDATE

    def test_listing_candidate_rule_triggers_when_score_above_threshold(self) -> None:
        """Rule triggers when listing score is above threshold."""
        rule = ListingCandidateRule(threshold=70)
        data = {
            "symbol": "ABC",
            "name": "ABC Token",
            "listing_score": 85,
            "signals": ["DEX volume grew 340%", "Social mentions up 500%"],
            "probability": "high",
            "likely_exchanges": ["Binance", "OKX"],
        }
        result = rule.evaluate(data)
        assert result is True

    def test_listing_candidate_rule_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when listing score is below threshold."""
        rule = ListingCandidateRule(threshold=70)
        data = {
            "symbol": "XYZ",
            "name": "XYZ Token",
            "listing_score": 50,
            "signals": [],
            "probability": "low",
            "likely_exchanges": [],
        }
        result = rule.evaluate(data)
        assert result is False

    def test_listing_candidate_rule_at_exact_threshold(self) -> None:
        """Rule triggers when score equals threshold."""
        rule = ListingCandidateRule(threshold=70)
        data = {
            "symbol": "DEF",
            "name": "DEF Token",
            "listing_score": 70,
            "signals": ["Some signal"],
            "probability": "medium",
            "likely_exchanges": ["Coinbase"],
        }
        result = rule.evaluate(data)
        assert result is True


class TestWhaleAccumulationRule:
    """Test WhaleAccumulationRule trigger conditions."""

    def test_whale_accumulation_rule_alert_type(self) -> None:
        """WhaleAccumulationRule has correct alert type."""
        rule = WhaleAccumulationRule()
        assert rule.alert_type == AlertType.WHALE_ACCUMULATION

    def test_whale_accumulation_triggers_when_score_above_threshold(self) -> None:
        """Rule triggers when whale score is above threshold."""
        rule = WhaleAccumulationRule(threshold=7.0)
        data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "whale_score": 8.5,
            "top10_change_pct": 15.0,
            "large_transactions": 50,
            "period_days": 7,
        }
        result = rule.evaluate(data)
        assert result is True

    def test_whale_accumulation_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when whale score is below threshold."""
        rule = WhaleAccumulationRule(threshold=7.0)
        data = {
            "symbol": "DOGE",
            "name": "Dogecoin",
            "whale_score": 3.0,
            "top10_change_pct": -5.0,
            "large_transactions": 10,
            "period_days": 7,
        }
        result = rule.evaluate(data)
        assert result is False


class TestRugpullRiskRule:
    """Test RugpullRiskRule trigger conditions."""

    def test_rugpull_risk_rule_alert_type(self) -> None:
        """RugpullRiskRule has correct alert type."""
        rule = RugpullRiskRule()
        assert rule.alert_type == AlertType.RUGPULL_RISK

    def test_rugpull_risk_triggers_when_score_above_threshold(self) -> None:
        """Rule triggers when risk score is above threshold."""
        rule = RugpullRiskRule(threshold=0.6)
        data = {
            "symbol": "SCAM",
            "name": "Scam Token",
            "risk_score": 0.85,
            "risk_factors": ["No liquidity lock", "Anonymous team", "Honeypot contract"],
        }
        result = rule.evaluate(data)
        assert result is True

    def test_rugpull_risk_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when risk score is below threshold."""
        rule = RugpullRiskRule(threshold=0.6)
        data = {
            "symbol": "SAFE",
            "name": "Safe Token",
            "risk_score": 0.2,
            "risk_factors": [],
        }
        result = rule.evaluate(data)
        assert result is False


class TestManipulationDetectedRule:
    """Test ManipulationDetectedRule trigger conditions."""

    def test_manipulation_detected_rule_alert_type(self) -> None:
        """ManipulationDetectedRule has correct alert type."""
        rule = ManipulationDetectedRule()
        assert rule.alert_type == AlertType.MANIPULATION_DETECTED

    def test_manipulation_triggers_when_confidence_above_threshold(self) -> None:
        """Rule triggers when manipulation confidence is above threshold."""
        rule = ManipulationDetectedRule(threshold=0.7)
        data = {
            "symbol": "PUMP",
            "name": "Pump Token",
            "manipulation_type": "wash_trading",
            "confidence": 0.85,
            "indicators": ["Circular transactions", "Fake volume"],
        }
        result = rule.evaluate(data)
        assert result is True

    def test_manipulation_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when confidence is below threshold."""
        rule = ManipulationDetectedRule(threshold=0.7)
        data = {
            "symbol": "LEGIT",
            "name": "Legit Token",
            "manipulation_type": "unknown",
            "confidence": 0.3,
            "indicators": [],
        }
        result = rule.evaluate(data)
        assert result is False


class TestTokenUnlockRule:
    """Test TokenUnlockRule trigger conditions."""

    def test_token_unlock_rule_alert_type(self) -> None:
        """TokenUnlockRule has correct alert type."""
        rule = TokenUnlockRule()
        assert rule.alert_type == AlertType.TOKEN_UNLOCK_SOON

    def test_token_unlock_triggers_when_pct_above_threshold(self) -> None:
        """Rule triggers when unlock percentage is above threshold."""
        rule = TokenUnlockRule(pct_threshold=5.0)
        data = {
            "symbol": "OP",
            "name": "Optimism",
            "unlock_pct": 10.5,
            "unlock_date": datetime(2024, 3, 15),
            "unlock_usd_value": 50_000_000,
        }
        result = rule.evaluate(data)
        assert result is True

    def test_token_unlock_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when unlock percentage is below threshold."""
        rule = TokenUnlockRule(pct_threshold=5.0)
        data = {
            "symbol": "ARB",
            "name": "Arbitrum",
            "unlock_pct": 2.0,
            "unlock_date": datetime(2024, 4, 1),
            "unlock_usd_value": 10_000_000,
        }
        result = rule.evaluate(data)
        assert result is False


class TestNarrativeEmergingRule:
    """Test NarrativeEmergingRule trigger conditions."""

    def test_narrative_emerging_rule_alert_type(self) -> None:
        """NarrativeEmergingRule has correct alert type."""
        rule = NarrativeEmergingRule()
        assert rule.alert_type == AlertType.NARRATIVE_EMERGING

    def test_narrative_emerging_triggers_when_momentum_above_threshold(self) -> None:
        """Rule triggers when momentum score is above threshold."""
        rule = NarrativeEmergingRule(threshold=7.0)
        data = {
            "narrative": "AI Agents",
            "momentum_score": 9.0,
            "top_tokens": ["AGIX", "FET", "OCEAN"],
            "mention_growth_pct": 250,
        }
        result = rule.evaluate(data)
        assert result is True

    def test_narrative_emerging_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when momentum is below threshold."""
        rule = NarrativeEmergingRule(threshold=7.0)
        data = {
            "narrative": "Old Narrative",
            "momentum_score": 3.0,
            "top_tokens": ["OLD1", "OLD2"],
            "mention_growth_pct": 10,
        }
        result = rule.evaluate(data)
        assert result is False


class TestMemecoinHypeRule:
    """Test MemecoinHypeRule trigger conditions."""

    def test_memecoin_hype_rule_alert_type(self) -> None:
        """MemecoinHypeRule has correct alert type."""
        rule = MemecoinHypeRule()
        assert rule.alert_type == AlertType.MEMECOIN_HYPE_DETECTED

    def test_memecoin_hype_triggers_when_social_growth_above_threshold(self) -> None:
        """Rule triggers when social growth is above threshold."""
        rule = MemecoinHypeRule(social_threshold=100)
        data = {
            "symbol": "PEPE",
            "name": "Pepe",
            "social_growth_pct": 500,
            "volume_growth_pct": 300,
            "holder_growth_pct": 150,
        }
        result = rule.evaluate(data)
        assert result is True

    def test_memecoin_hype_does_not_trigger_below_threshold(self) -> None:
        """Rule does not trigger when social growth is below threshold."""
        rule = MemecoinHypeRule(social_threshold=100)
        data = {
            "symbol": "SHIB",
            "name": "Shiba Inu",
            "social_growth_pct": 20,
            "volume_growth_pct": 10,
            "holder_growth_pct": 5,
        }
        result = rule.evaluate(data)
        assert result is False


class TestAlertRuleEngine:
    """Test AlertRuleEngine — evaluates all rules and returns triggered alerts."""

    def test_engine_init_creates_instance(self) -> None:
        """AlertRuleEngine can be initialized."""
        engine = AlertRuleEngine()
        assert engine is not None

    def test_engine_has_register_rule_method(self) -> None:
        """Engine has register_rule method."""
        engine = AlertRuleEngine()
        assert hasattr(engine, "register_rule")
        assert callable(engine.register_rule)

    def test_engine_has_evaluate_all_method(self) -> None:
        """Engine has evaluate_all method."""
        engine = AlertRuleEngine()
        assert hasattr(engine, "evaluate_all")
        assert callable(engine.evaluate_all)

    def test_engine_register_rule_adds_rule(self) -> None:
        """Registering a rule adds it to the engine."""
        engine = AlertRuleEngine()
        rule = ListingCandidateRule()
        engine.register_rule(rule)
        assert len(engine.rules) == 1

    def test_engine_evaluate_all_returns_triggered_alerts(self) -> None:
        """evaluate_all returns list of triggered alert data."""
        engine = AlertRuleEngine()
        rule = ListingCandidateRule(threshold=70)
        engine.register_rule(rule)

        data = {
            "symbol": "ABC",
            "name": "ABC Token",
            "listing_score": 85,
            "signals": ["Signal 1"],
            "probability": "high",
            "likely_exchanges": ["Binance"],
        }

        results = engine.evaluate_all(data)
        assert len(results) == 1
        assert results[0]["alert_type"] == AlertType.LISTING_CANDIDATE
        assert results[0]["data"] == data

    def test_engine_evaluate_all_returns_empty_when_no_triggers(self) -> None:
        """evaluate_all returns empty list when no rules trigger."""
        engine = AlertRuleEngine()
        rule = ListingCandidateRule(threshold=70)
        engine.register_rule(rule)

        data = {
            "symbol": "XYZ",
            "name": "XYZ Token",
            "listing_score": 30,
            "signals": [],
            "probability": "low",
            "likely_exchanges": [],
        }

        results = engine.evaluate_all(data)
        assert len(results) == 0

    def test_engine_evaluate_all_with_multiple_rules(self) -> None:
        """evaluate_all checks all registered rules."""
        engine = AlertRuleEngine()
        engine.register_rule(ListingCandidateRule(threshold=70))
        engine.register_rule(WhaleAccumulationRule(threshold=7.0))

        data = {
            "symbol": "MEGA",
            "name": "Mega Token",
            "listing_score": 85,
            "signals": ["Signal"],
            "probability": "high",
            "likely_exchanges": ["Binance"],
            "whale_score": 8.5,
            "top10_change_pct": 20.0,
            "large_transactions": 100,
            "period_days": 7,
        }

        results = engine.evaluate_all(data)
        assert len(results) == 2
        alert_types = [r["alert_type"] for r in results]
        assert AlertType.LISTING_CANDIDATE in alert_types
        assert AlertType.WHALE_ACCUMULATION in alert_types

    def test_engine_create_default_registers_all_rules(self) -> None:
        """create_default factory registers all standard rules."""
        engine = AlertRuleEngine.create_default()
        # Should have all 7 rules (not daily report, that's different)
        assert len(engine.rules) == 7
