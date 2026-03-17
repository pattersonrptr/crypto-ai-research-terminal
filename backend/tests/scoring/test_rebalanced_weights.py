"""TDD tests for rebalanced pillar weights.

Item 5 of Ranking Credibility Sprint: risk weight increases from 0.10
to 0.30 so risky tokens (memecoins, micro-caps) get properly penalised.
Other weights reduced proportionally.

New defaults: fundamental=0.25, growth=0.20, narrative=0.15, listing=0.10, risk=0.30
"""

from __future__ import annotations

import pytest

from app.scoring.opportunity_engine import OpportunityEngine
from app.scoring.weight_service import DEFAULT_WEIGHTS


class TestRebalancedDefaultWeights:
    """DEFAULT_WEIGHTS must reflect the new risk-heavy distribution."""

    def test_risk_weight_is_030(self) -> None:
        assert DEFAULT_WEIGHTS["risk"] == pytest.approx(0.30)

    def test_fundamental_weight_is_025(self) -> None:
        assert DEFAULT_WEIGHTS["fundamental"] == pytest.approx(0.25)

    def test_growth_weight_is_020(self) -> None:
        assert DEFAULT_WEIGHTS["growth"] == pytest.approx(0.20)

    def test_narrative_weight_is_015(self) -> None:
        assert DEFAULT_WEIGHTS["narrative"] == pytest.approx(0.15)

    def test_listing_weight_is_010(self) -> None:
        assert DEFAULT_WEIGHTS["listing"] == pytest.approx(0.10)

    def test_weights_sum_to_one(self) -> None:
        total = sum(v for k, v in DEFAULT_WEIGHTS.items() if k != "source")
        assert total == pytest.approx(1.0)


class TestHighRiskWeightPenalisesRiskyTokens:
    """With risk=0.30, a token with low risk_score should rank much lower."""

    def test_risky_token_scores_lower_than_safe_token(self) -> None:
        """A risky token (risk=0.2) must score significantly lower
        than a safe token (risk=0.9) even with identical other scores."""
        safe_score = OpportunityEngine.full_composite_score(
            fundamental=0.5,
            growth=0.5,
            narrative=0.5,
            listing=0.5,
            risk=0.9,
        )
        risky_score = OpportunityEngine.full_composite_score(
            fundamental=0.5,
            growth=0.5,
            narrative=0.5,
            listing=0.5,
            risk=0.2,
        )
        # With risk=0.30, the difference must be >= 0.20
        assert safe_score - risky_score >= 0.20

    def test_default_weights_used_when_none_passed(self) -> None:
        """full_composite_score(weights=None) must use the new defaults."""
        # With new defaults, risk contributes 30% of the score
        score = OpportunityEngine.full_composite_score(
            fundamental=0.5,
            growth=0.5,
            narrative=0.5,
            listing=0.5,
            risk=1.0,
        )
        # base = 0.25*0.5 + 0.20*0.5 + 0.15*0.5 + 0.10*0.5 + 0.30*1.0
        #      = 0.125 + 0.10 + 0.075 + 0.05 + 0.30 = 0.65
        assert score == pytest.approx(0.65, abs=0.01)
