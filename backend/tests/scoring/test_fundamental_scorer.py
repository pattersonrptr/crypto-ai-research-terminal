"""Tests for FundamentalScorer.

Uses static weights — no LLM involved at this phase.

Phase 1: 4-metric market-data scorer (``score()``).
Phase 9: 5-sub-pillar model (``sub_pillar_score()``): technology, tokenomics,
         adoption, dev_activity, narrative — each 20%.
"""

import pytest

from app.exceptions import ScoringError
from app.scoring.fundamental_scorer import FundamentalScorer


class TestFundamentalScorerScore:
    """FundamentalScorer.score() returns a float in [0, 1]."""

    def test_fundamental_scorer_score_returns_float_between_zero_and_one(self) -> None:
        data = {
            "volume_mcap_ratio": 0.1,
            "price_velocity": 5.0,
            "ath_distance_pct": 50.0,
            "market_cap_usd": 1_000_000_000.0,
        }
        result = FundamentalScorer.score(data)
        assert 0.0 <= result <= 1.0

    def test_fundamental_scorer_score_high_quality_data_scores_higher(self) -> None:
        strong = {
            "volume_mcap_ratio": 0.3,
            "price_velocity": 20.0,
            "ath_distance_pct": 80.0,
            "market_cap_usd": 5_000_000_000.0,
        }
        weak = {
            "volume_mcap_ratio": 0.01,
            "price_velocity": -20.0,
            "ath_distance_pct": 5.0,
            "market_cap_usd": 100_000.0,
        }
        assert FundamentalScorer.score(strong) > FundamentalScorer.score(weak)

    def test_fundamental_scorer_score_raises_scoring_error_on_missing_fields(self) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.score({})

    def test_fundamental_scorer_score_raises_scoring_error_on_negative_market_cap(
        self,
    ) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.score(
                {
                    "volume_mcap_ratio": 0.1,
                    "price_velocity": 0.0,
                    "ath_distance_pct": 30.0,
                    "market_cap_usd": -1.0,
                }
            )


# ---------------------------------------------------------------------------
# Phase 9 — 5-sub-pillar model
# ---------------------------------------------------------------------------


class TestFundamentalScorerSubPillarScore:
    """FundamentalScorer.sub_pillar_score() combines 5 pillars at 20% each."""

    def test_sub_pillar_score_returns_float_in_range(self) -> None:
        result = FundamentalScorer.sub_pillar_score(
            technology=0.7,
            tokenomics=0.6,
            adoption=0.8,
            dev_activity=0.5,
            narrative=0.4,
        )
        assert 0.0 <= result <= 1.0

    def test_sub_pillar_score_equal_weights_at_20_percent(self) -> None:
        """All pillars at 1.0 → composite = 1.0."""
        result = FundamentalScorer.sub_pillar_score(
            technology=1.0,
            tokenomics=1.0,
            adoption=1.0,
            dev_activity=1.0,
            narrative=1.0,
        )
        assert result == pytest.approx(1.0)

    def test_sub_pillar_score_all_zeros(self) -> None:
        result = FundamentalScorer.sub_pillar_score(
            technology=0.0,
            tokenomics=0.0,
            adoption=0.0,
            dev_activity=0.0,
            narrative=0.0,
        )
        assert result == pytest.approx(0.0)

    def test_sub_pillar_score_single_pillar_at_one(self) -> None:
        """Only technology at 1.0, rest 0.0 → composite = 0.20."""
        result = FundamentalScorer.sub_pillar_score(
            technology=1.0,
            tokenomics=0.0,
            adoption=0.0,
            dev_activity=0.0,
            narrative=0.0,
        )
        assert result == pytest.approx(0.20)

    def test_sub_pillar_score_raises_on_out_of_range(self) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.sub_pillar_score(
                technology=1.5,
                tokenomics=0.5,
                adoption=0.5,
                dev_activity=0.5,
                narrative=0.5,
            )

    def test_sub_pillar_score_raises_on_negative(self) -> None:
        with pytest.raises(ScoringError):
            FundamentalScorer.sub_pillar_score(
                technology=-0.1,
                tokenomics=0.5,
                adoption=0.5,
                dev_activity=0.5,
                narrative=0.5,
            )

    def test_sub_pillar_score_strong_beats_weak(self) -> None:
        strong = FundamentalScorer.sub_pillar_score(
            technology=0.9,
            tokenomics=0.8,
            adoption=0.7,
            dev_activity=0.8,
            narrative=0.6,
        )
        weak = FundamentalScorer.sub_pillar_score(
            technology=0.2,
            tokenomics=0.1,
            adoption=0.15,
            dev_activity=0.1,
            narrative=0.05,
        )
        assert strong > weak
