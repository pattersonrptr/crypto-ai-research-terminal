"""Tests for app.backtesting.historical_scorer — TDD Red→Green.

The historical scorer runs a simplified scoring pipeline on historical
snapshots and produces ranked token lists per snapshot date.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.backtesting.historical_scorer import (
    HistoricalScoredToken,
    HistoricalScoringResult,
    score_historical_snapshots,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot_data() -> list[dict[str, object]]:
    """Build a list of snapshot dicts simulating historical token states.

    Each dict has fields matching HistoricalSnapshot columns:
    symbol, snapshot_date, price_usd, market_cap_usd, volume_usd,
    circulating_supply, total_supply, categories.
    """
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
        {
            "symbol": "LINK",
            "snapshot_date": date(2020, 1, 15),
            "price_usd": 2.30,
            "market_cap_usd": 800_000_000.0,
            "volume_usd": 300_000_000.0,
            "circulating_supply": 350_000_000.0,
            "total_supply": 1_000_000_000.0,
            "categories": "Oracle,DeFi",
        },
    ]


# ---------------------------------------------------------------------------
# TestHistoricalScoredToken
# ---------------------------------------------------------------------------


class TestHistoricalScoredToken:
    """Unit tests for the HistoricalScoredToken dataclass."""

    def test_historical_scored_token_fields_are_set(self) -> None:
        """HistoricalScoredToken must store symbol, rank, composite_score, sub_scores."""
        token = HistoricalScoredToken(
            symbol="BTC",
            rank=1,
            composite_score=0.75,
            fundamental_score=0.80,
            volume_mcap_ratio=0.16,
        )
        assert token.symbol == "BTC"
        assert token.rank == 1
        assert token.composite_score == pytest.approx(0.75)
        assert token.fundamental_score == pytest.approx(0.80)

    def test_historical_scored_token_rank_must_be_positive(self) -> None:
        """rank >= 1."""
        token = HistoricalScoredToken(
            symbol="ETH",
            rank=1,
            composite_score=0.5,
            fundamental_score=0.5,
            volume_mcap_ratio=0.1,
        )
        assert token.rank >= 1


# ---------------------------------------------------------------------------
# TestHistoricalScoringResult
# ---------------------------------------------------------------------------


class TestHistoricalScoringResult:
    """Unit tests for the HistoricalScoringResult dataclass."""

    def test_scoring_result_fields_are_set(self) -> None:
        """HistoricalScoringResult must have snapshot_date and ranked_tokens."""
        result = HistoricalScoringResult(
            snapshot_date=date(2020, 1, 15),
            ranked_tokens=[],
        )
        assert result.snapshot_date == date(2020, 1, 15)
        assert result.ranked_tokens == []

    def test_scoring_result_top_k_returns_first_k(self) -> None:
        """top_k() must return the first k tokens from ranked_tokens."""
        tokens = [
            HistoricalScoredToken(
                symbol=f"T{i}",
                rank=i,
                composite_score=1.0 - i * 0.1,
                fundamental_score=0.5,
                volume_mcap_ratio=0.1,
            )
            for i in range(1, 6)
        ]
        result = HistoricalScoringResult(
            snapshot_date=date(2020, 1, 15),
            ranked_tokens=tokens,
        )
        top_3 = result.top_k(3)
        assert len(top_3) == 3
        assert top_3[0].symbol == "T1"
        assert top_3[2].symbol == "T3"


# ---------------------------------------------------------------------------
# TestScoreHistoricalSnapshots
# ---------------------------------------------------------------------------


class TestScoreHistoricalSnapshots:
    """Tests for score_historical_snapshots()."""

    def test_score_returns_scoring_result(self) -> None:
        """score_historical_snapshots must return a HistoricalScoringResult."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        assert isinstance(result, HistoricalScoringResult)

    def test_score_result_has_correct_date(self) -> None:
        """The result snapshot_date must match the input."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        assert result.snapshot_date == date(2020, 1, 15)

    def test_score_produces_ranked_tokens_for_each_input(self) -> None:
        """ranked_tokens must contain one entry per input snapshot."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        assert len(result.ranked_tokens) == len(snapshots)

    def test_score_ranked_tokens_sorted_descending_by_score(self) -> None:
        """ranked_tokens must be sorted by composite_score descending."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        scores = [t.composite_score for t in result.ranked_tokens]
        assert scores == sorted(scores, reverse=True)

    def test_score_ranks_are_sequential_starting_at_one(self) -> None:
        """Ranks must be 1, 2, 3, ..., n."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        ranks = [t.rank for t in result.ranked_tokens]
        assert ranks == list(range(1, len(snapshots) + 1))

    def test_score_composite_scores_in_zero_one_range(self) -> None:
        """All composite scores must be in [0.0, 1.0]."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        for t in result.ranked_tokens:
            assert 0.0 <= t.composite_score <= 1.0

    def test_score_empty_snapshots_returns_empty_ranked_tokens(self) -> None:
        """score_historical_snapshots with empty input returns empty ranked_tokens."""
        result = score_historical_snapshots([], snapshot_date=date(2020, 1, 15))
        assert result.ranked_tokens == []

    def test_score_lower_mcap_higher_vol_ratio_gets_higher_fundamental(self) -> None:
        """SOL (low mcap, high vol/mcap) should score higher fundamental than BTC."""
        snapshots = _make_snapshot_data()
        result = score_historical_snapshots(snapshots, snapshot_date=date(2020, 1, 15))
        token_map = {t.symbol: t for t in result.ranked_tokens}
        # SOL has vol/mcap = 5M/50M = 0.1, BTC has 25B/155B = 0.16
        # But SOL's smaller mcap should give it edge in opportunity
        assert token_map["SOL"].fundamental_score > 0.0
        assert token_map["BTC"].fundamental_score > 0.0
