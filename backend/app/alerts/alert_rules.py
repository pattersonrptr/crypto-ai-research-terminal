"""AlertRules — defines trigger conditions for alerts.

Each rule evaluates token/market data and determines if an alert
should be triggered based on configurable thresholds.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.alerts.alert_formatter import AlertType


class AlertRule(ABC):
    """Base class for all alert rules."""

    @property
    @abstractmethod
    def alert_type(self) -> AlertType:
        """Return the type of alert this rule produces."""
        ...

    @abstractmethod
    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate whether the rule should trigger an alert.

        Args:
            data: Dictionary containing relevant data for evaluation.

        Returns:
            True if alert should be triggered, False otherwise.
        """
        ...


class ListingCandidateRule(AlertRule):
    """Rule for detecting potential exchange listing candidates."""

    def __init__(self, threshold: int = 70) -> None:
        """Initialize rule with threshold.

        Args:
            threshold: Minimum listing score (0-100) to trigger alert.
        """
        self._threshold = threshold

    @property
    def alert_type(self) -> AlertType:
        """Return LISTING_CANDIDATE alert type."""
        return AlertType.LISTING_CANDIDATE

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if token is a listing candidate.

        Args:
            data: Must contain 'listing_score' key.

        Returns:
            True if listing_score >= threshold.
        """
        listing_score: int = data.get("listing_score", 0)
        return listing_score >= self._threshold


class WhaleAccumulationRule(AlertRule):
    """Rule for detecting whale accumulation patterns."""

    def __init__(self, threshold: float = 7.0) -> None:
        """Initialize rule with threshold.

        Args:
            threshold: Minimum whale score (0-10) to trigger alert.
        """
        self._threshold = threshold

    @property
    def alert_type(self) -> AlertType:
        """Return WHALE_ACCUMULATION alert type."""
        return AlertType.WHALE_ACCUMULATION

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if whale accumulation is detected.

        Args:
            data: Must contain 'whale_score' key.

        Returns:
            True if whale_score >= threshold.
        """
        whale_score: float = data.get("whale_score", 0)
        return whale_score >= self._threshold


class RugpullRiskRule(AlertRule):
    """Rule for detecting high rugpull risk tokens."""

    def __init__(self, threshold: float = 0.6) -> None:
        """Initialize rule with threshold.

        Args:
            threshold: Minimum risk score (0-1) to trigger alert.
        """
        self._threshold = threshold

    @property
    def alert_type(self) -> AlertType:
        """Return RUGPULL_RISK alert type."""
        return AlertType.RUGPULL_RISK

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if token has high rugpull risk.

        Args:
            data: Must contain 'risk_score' key.

        Returns:
            True if risk_score >= threshold.
        """
        risk_score: float = data.get("risk_score", 0)
        return risk_score >= self._threshold


class ManipulationDetectedRule(AlertRule):
    """Rule for detecting market manipulation."""

    def __init__(self, threshold: float = 0.7) -> None:
        """Initialize rule with threshold.

        Args:
            threshold: Minimum confidence (0-1) to trigger alert.
        """
        self._threshold = threshold

    @property
    def alert_type(self) -> AlertType:
        """Return MANIPULATION_DETECTED alert type."""
        return AlertType.MANIPULATION_DETECTED

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if manipulation is detected with high confidence.

        Args:
            data: Must contain 'confidence' key.

        Returns:
            True if confidence >= threshold.
        """
        confidence: float = data.get("confidence", 0)
        return confidence >= self._threshold


class TokenUnlockRule(AlertRule):
    """Rule for detecting significant upcoming token unlocks."""

    def __init__(self, pct_threshold: float = 5.0) -> None:
        """Initialize rule with threshold.

        Args:
            pct_threshold: Minimum unlock percentage to trigger alert.
        """
        self._pct_threshold = pct_threshold

    @property
    def alert_type(self) -> AlertType:
        """Return TOKEN_UNLOCK_SOON alert type."""
        return AlertType.TOKEN_UNLOCK_SOON

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if token unlock is significant.

        Args:
            data: Must contain 'unlock_pct' key.

        Returns:
            True if unlock_pct >= threshold.
        """
        unlock_pct: float = data.get("unlock_pct", 0)
        return unlock_pct >= self._pct_threshold


class NarrativeEmergingRule(AlertRule):
    """Rule for detecting emerging market narratives."""

    def __init__(self, threshold: float = 7.0) -> None:
        """Initialize rule with threshold.

        Args:
            threshold: Minimum momentum score (0-10) to trigger alert.
        """
        self._threshold = threshold

    @property
    def alert_type(self) -> AlertType:
        """Return NARRATIVE_EMERGING alert type."""
        return AlertType.NARRATIVE_EMERGING

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if narrative is gaining significant momentum.

        Args:
            data: Must contain 'momentum_score' key.

        Returns:
            True if momentum_score >= threshold.
        """
        momentum_score: float = data.get("momentum_score", 0)
        return momentum_score >= self._threshold


class MemecoinHypeRule(AlertRule):
    """Rule for detecting memecoin hype patterns."""

    def __init__(self, social_threshold: int = 100) -> None:
        """Initialize rule with threshold.

        Args:
            social_threshold: Minimum social growth % to trigger alert.
        """
        self._social_threshold = social_threshold

    @property
    def alert_type(self) -> AlertType:
        """Return MEMECOIN_HYPE_DETECTED alert type."""
        return AlertType.MEMECOIN_HYPE_DETECTED

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate if memecoin is experiencing viral growth.

        Args:
            data: Must contain 'social_growth_pct' key.

        Returns:
            True if social_growth_pct >= threshold.
        """
        social_growth_pct: int = data.get("social_growth_pct", 0)
        return social_growth_pct >= self._social_threshold


class AlertRuleEngine:
    """Engine that evaluates all registered rules against data."""

    def __init__(self) -> None:
        """Initialize engine with empty rule list."""
        self._rules: list[AlertRule] = []

    @property
    def rules(self) -> list[AlertRule]:
        """Return list of registered rules."""
        return self._rules

    def register_rule(self, rule: AlertRule) -> None:
        """Register a rule with the engine.

        Args:
            rule: AlertRule instance to register.
        """
        self._rules.append(rule)

    def evaluate_all(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate all registered rules against the data.

        Args:
            data: Data to evaluate rules against.

        Returns:
            List of dicts with 'alert_type' and 'data' for triggered rules.
        """
        triggered: list[dict[str, Any]] = []
        for rule in self._rules:
            if rule.evaluate(data):
                triggered.append({"alert_type": rule.alert_type, "data": data})
        return triggered

    @classmethod
    def create_default(cls) -> "AlertRuleEngine":
        """Create an engine with all default rules registered.

        Returns:
            AlertRuleEngine with standard rules.
        """
        engine = cls()
        engine.register_rule(ListingCandidateRule())
        engine.register_rule(WhaleAccumulationRule())
        engine.register_rule(RugpullRiskRule())
        engine.register_rule(ManipulationDetectedRule())
        engine.register_rule(TokenUnlockRule())
        engine.register_rule(NarrativeEmergingRule())
        engine.register_rule(MemecoinHypeRule())
        return engine
