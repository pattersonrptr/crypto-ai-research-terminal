"""Tests for upgraded historical_scorer — WeightSet-aware scoring.

TDD: RED phase — tests for configurable weights and per-pillar sub-scores.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.backtesting.historical_scorer import (
    HistoricalScoredToken,
    HistoricalScoringResult,
    score_historical_snapshots,
)
from app.backtesting.weight_calibrator import WeightSet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_snapshot_data() -> list[dict[str, object]]:
    """Snapshot dicts simulating historical token states."""
    return [
        {
            "symbol": "BTC",
            "snapshot_date": date(2020, 1, 15),
            "price_usd": 8_500.0,
            "market_cap_usd": 155_000_000_000.0,
            "volume_usd": 25_000_000_000.0,
            "circulating_supply": 18_200_000.0,
            "total_supply": 21_000_000.0,
            "categories": "Store of Value,Layer 1",
        },
        {
            "symbol": "ETH",
            "snapshot_date": date(2020, 1, 15),
            "price_usd": 165.0,
            "market_cap_usd": 18_000_000_000.0,
            "volume_usd": 8_000_000_000.0,
            "circulating_supply": 109_000_000.0,
            "total_supply": None,
            "categories": "Smart Contract Platform,Layer 1",
        },
        {
            "symbol": "SOL",
            "snapshot_date": date(2020, 1, 15),
            "price_usd": 0.50,
            "market_cap_usd": 50_000_000.0,
            "volume_usd": 5_000_000.0,
            "circulating_supply": 100_000_000.0,
            "total_supply": 500_000_000.0,
            "categories": "Smart Contract Platform,Layer 1",
        },
    ]


# ---------------------------------------------------------------------------
# Tests: WeightSet-aware scoring
# ---------------------------------------------------------------------------


class TestScoreWithWeights:
    """Tests for score_historical_snapshots with explicit WeightSet."""

    def test_accepts_weight_set_parameter(self) -> None:
        """score_historical_snapshots must accept an optional weights parameter."""
        ws = WeightSet(
            fundamental=0.50,
            growth=0.20,
            narrative=0.10,
            listing=0.10,
            risk=0.10,
        )
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(
            snapshots,
            snapshot_date=date(2020, 1, 15),
            weights=ws,
        )
        assert isinstance(result, HistoricalScoringResult)
        assert len(result.ranked_tokens) == 3

    def test_default_weights_match_phase9(self) -> None:
        """Without explicit weights, results must equal the default Phase 9 behavior."""
        snapshots = _make_snapshot_data()
        result_default = score_historical_snapshots(
            snapshots, snapshot_date=date(2020, 1, 15),
        )
        phase9_ws = WeightSet(
            fundamental=0.30, growth=0.25, narrative=0.20,
            listing=0.15, risk=0.10,
        )
        result_explicit = score_historical_snapshots(
            snapshots, snapshot_date=date(2020, 1, 15), weights=phase9_ws,
        )
        for d, e in zip(
            result_default.ranked_tokens, result_explicit.ranked_tokens, strict=True,
        ):
            assert d.symbol == e.symbol
            assert d.composite_score == pytest.approx(e.composite_score)

    def test_higher_fundamental_weight_changes_ranking(self) -> None:
        """Increasing fundamental weight should boost tokens with higher fundamental score."""
        snapshots = _make_snapshot_data()

        low_fund = WeightSet(fundamental=0.10, growth=0.30, narrative=0.30, listing=0.20, risk=0.10)
        high_fund = WeightSet(fundamental=0.80, growth=0.05, narrative=0.05, listing=0.05, risk=0.05)

        result_low = score_historical_snapshots(
            snapshots, snapshot_date=date(2020, 1, 15), weights=low_fund,
        )
        result_high = score_historical_snapshots(
            snapshots, snapshot_date=date(2020, 1, 15), weights=high_fund,
        )

        # With high fundamental weight, SOL (small mcap, high vol/mcap) should
        # score relatively higher vs the low_fund scenario.
        scores_high = {t.symbol: t.composite_score for t in result_high.ranked_tokens}
        scores_low = {t.symbol: t.composite_score for t in result_low.ranked_tokens}

        # SOL should have a bigger gap from BTC with high fundamental weight
        sol_advantage_high = scores_high["SOL"] - scores_high["BTC"]
        sol_advantage_low = scores_low["SOL"] - scores_low["BTC"]
        assert sol_advantage_high > sol_advantage_low

    def test_all_zero_fundamental_weight_equalises_scores(self) -> None:
        """If fundamental weight is 0, all tokens get the same composite score
        (since other pillars default to 0.5 neutral)."""
        snapshots = _make_snapshot_data()
        ws = WeightSet(fundamental=0.00, growth=0.30, narrative=0.30, listing=0.20, risk=0.20)
        result = score_historical_snapshots(
            snapshots, snapshot_date=date(2020, 1, 15), weights=ws,
        )
        scores = [t.composite_score for t in result.ranked_tokens]
        # All should be equal (neutral)
        assert all(s == pytest.approx(scores[0]) for s in scores)


# ---------------------------------------------------------------------------
# Tests: Per-pillar sub-scores exposed
# ---------------------------------------------------------------------------


class TestPerPillarSubScores:
    """HistoricalScoredToken must expose all 5 pillar sub-scores."""

    def test_scored_token_has_growth_score(self) -> None:
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert hasattr(t, "growth_score")
            assert isinstance(t.growth_score, float)

    def test_scored_token_has_narrative_score(self) -> None:
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert hasattr(t, "narrative_score")
            assert isinstance(t.narrative_score, float)

    def test_scored_token_has_listing_score(self) -> None:
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert hasattr(t, "listing_score")
            assert isinstance(t.listing_score, float)

    def test_scored_token_has_risk_score(self) -> None:
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert hasattr(t, "risk_score")
            assert isinstance(t.risk_score, float)

    def test_neutral_pillar_scores_are_0_5(self) -> None:
        """Pillars without historical data default to 0.5."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert t.growth_score == pytest.approx(0.5)
            assert t.narrative_score == pytest.approx(0.5)
            assert t.listing_score == pytest.approx(0.5)
            assert t.risk_score == pytest.approx(0.5)
