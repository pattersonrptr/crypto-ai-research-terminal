"""TDD tests for scoring/score_explainer.py — ScoreExplainer.explain().

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

import pytest

from app.scoring.score_explainer import PillarExplanation, ScoreExplainer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _base_token_data() -> dict:
    """Return a minimal token data dict with all required fields."""
    return {
        "symbol": "ETH",
        "name": "Ethereum",
        "fundamental_score": 0.75,
        "technology_score": 0.80,
        "tokenomics_score": 0.70,
        "adoption_score": 0.65,
        "dev_activity_score": 0.85,
        "narrative_score": 0.60,
        "growth_score": 0.70,
        "risk_score": 0.50,
        "listing_probability": 0.30,
        "cycle_leader_prob": 0.10,
        "opportunity_score": 0.68,
        "price_usd": 3500.0,
        "market_cap_usd": 420_000_000_000,
        "volume_24h_usd": 15_000_000_000,
        "price_change_7d": 5.2,
        "reddit_subscribers": 1_500_000,
        "reddit_posts_24h": 120,
        "twitter_mentions_24h": 5000,
        "twitter_engagement": 25000,
        "sentiment_score": 0.7,
    }


# ---------------------------------------------------------------------------
# ScoreExplainer.explain tests
# ---------------------------------------------------------------------------


class TestScoreExplainerExplain:
    """Tests for ScoreExplainer.explain()."""

    def test_explain_returns_list_of_pillar_explanations(self) -> None:
        """explain() must return a list of PillarExplanation objects."""
        result = ScoreExplainer.explain(_base_token_data())
        assert isinstance(result, list)
        assert all(isinstance(p, PillarExplanation) for p in result)

    def test_explain_covers_all_five_pillars(self) -> None:
        """explain() must include all 5 scoring pillars + overall."""
        result = ScoreExplainer.explain(_base_token_data())
        pillar_names = {p.pillar for p in result}
        expected = {"fundamental", "growth", "narrative", "listing", "risk", "overall"}
        assert pillar_names == expected

    def test_explain_each_pillar_has_score_and_text(self) -> None:
        """Each PillarExplanation must have pillar, score, and explanation."""
        result = ScoreExplainer.explain(_base_token_data())
        for p in result:
            assert isinstance(p.pillar, str)
            assert isinstance(p.score, float)
            assert isinstance(p.explanation, str)
            assert len(p.explanation) > 10  # meaningful text

    def test_explain_fundamental_mentions_sub_pillars(self) -> None:
        """Fundamental explanation should mention technology/tokenomics/adoption."""
        result = ScoreExplainer.explain(_base_token_data())
        fundamental = next(p for p in result if p.pillar == "fundamental")
        text = fundamental.explanation.lower()
        # Should reference at least one sub-pillar
        assert any(word in text for word in ["technology", "tokenomics", "adoption", "dev"])

    def test_explain_growth_mentions_momentum(self) -> None:
        """Growth explanation should reference growth or momentum context."""
        result = ScoreExplainer.explain(_base_token_data())
        growth = next(p for p in result if p.pillar == "growth")
        assert growth.score == pytest.approx(0.70, abs=0.01)
        assert len(growth.explanation) > 10

    def test_explain_risk_high_score_positive_text(self) -> None:
        """High risk score (safer) should produce positive risk explanation."""
        data = _base_token_data()
        data["risk_score"] = 0.85
        result = ScoreExplainer.explain(data)
        risk = next(p for p in result if p.pillar == "risk")
        assert risk.score == pytest.approx(0.85, abs=0.01)

    def test_explain_risk_low_score_warning_text(self) -> None:
        """Low risk score should produce cautionary explanation."""
        data = _base_token_data()
        data["risk_score"] = 0.20
        result = ScoreExplainer.explain(data)
        risk = next(p for p in result if p.pillar == "risk")
        assert risk.score == pytest.approx(0.20, abs=0.01)

    def test_explain_missing_social_data_still_works(self) -> None:
        """explain() must not fail when social data fields are absent."""
        data = _base_token_data()
        del data["reddit_subscribers"]
        del data["twitter_mentions_24h"]
        del data["twitter_engagement"]
        del data["sentiment_score"]
        result = ScoreExplainer.explain(data)
        assert len(result) == 6

    def test_explain_pillar_explanation_to_dict(self) -> None:
        """PillarExplanation.to_dict() must return a serializable dict."""
        result = ScoreExplainer.explain(_base_token_data())
        for p in result:
            d = p.to_dict()
            assert d["pillar"] == p.pillar
            assert d["score"] == p.score
            assert d["explanation"] == p.explanation

    def test_explain_overall_summary_included(self) -> None:
        """explain() result should include an 'overall' summary."""
        result = ScoreExplainer.explain(_base_token_data())
        overall = next((p for p in result if p.pillar == "overall"), None)
        assert overall is not None
        assert overall.score == pytest.approx(0.68, abs=0.01)
        assert len(overall.explanation) > 10

    def test_explain_returns_six_entries_with_overall(self) -> None:
        """explain() returns 5 pillars + 1 overall = 6 entries."""
        result = ScoreExplainer.explain(_base_token_data())
        assert len(result) == 6


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestScoreExplainerEdgeCases:
    """Edge case and boundary tests for ScoreExplainer."""

    def test_explain_zero_scores(self) -> None:
        """All-zero scores should still produce valid explanations."""
        data = _base_token_data()
        for key in [
            "fundamental_score",
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "opportunity_score",
        ]:
            data[key] = 0.0
        result = ScoreExplainer.explain(data)
        assert len(result) == 6

    def test_explain_perfect_scores(self) -> None:
        """All-1.0 scores should produce valid explanations."""
        data = _base_token_data()
        for key in [
            "fundamental_score",
            "technology_score",
            "tokenomics_score",
            "adoption_score",
            "dev_activity_score",
            "narrative_score",
            "growth_score",
            "risk_score",
            "listing_probability",
            "opportunity_score",
        ]:
            data[key] = 1.0
        result = ScoreExplainer.explain(data)
        assert len(result) == 6

    def test_explain_missing_optional_fields_defaults(self) -> None:
        """Missing optional fields should use defaults without errors."""
        data = {
            "symbol": "NEW",
            "name": "NewCoin",
            "fundamental_score": 0.50,
            "technology_score": 0.50,
            "tokenomics_score": 0.50,
            "adoption_score": 0.50,
            "dev_activity_score": 0.50,
            "narrative_score": 0.50,
            "growth_score": 0.50,
            "risk_score": 0.50,
            "listing_probability": 0.50,
            "opportunity_score": 0.50,
        }
        result = ScoreExplainer.explain(data)
        assert len(result) == 6
