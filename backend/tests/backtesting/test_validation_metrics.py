"""Tests for app.backtesting.validation_metrics — TDD Red→Green.

Validation metrics measure how well the model's ranked recommendations
predict actual top performers in a subsequent market cycle.

Key metrics:
  - Precision@K: of the top-K recommended, how many were actual winners?
  - Recall@K: of all actual winners, how many were in our top-K?
  - Hit rate: fraction of recommended tokens that outperformed the market.
"""

from __future__ import annotations

import pytest

from app.backtesting.validation_metrics import (
    TokenOutcome,
    ValidationReport,
    compute_hit_rate,
    compute_precision_at_k,
    compute_recall_at_k,
    generate_validation_report,
)

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def _make_outcomes() -> list[TokenOutcome]:
    """Create a sample set of token outcomes.

    Ranked by model score (descending): A, B, C, D, E, F, G, H, I, J
    Actual multipliers: A=12x, B=2x, C=8x, D=0.5x, E=6x, F=1.5x, G=15x, H=0.3x, I=3x, J=20x
    Winners (>= 5x): A(12x), C(8x), E(6x), G(15x), J(20x) = 5 winners
    """
    return [
        TokenOutcome(symbol="A", model_rank=1, model_score=0.95, actual_multiplier=12.0),
        TokenOutcome(symbol="B", model_rank=2, model_score=0.90, actual_multiplier=2.0),
        TokenOutcome(symbol="C", model_rank=3, model_score=0.85, actual_multiplier=8.0),
        TokenOutcome(symbol="D", model_rank=4, model_score=0.80, actual_multiplier=0.5),
        TokenOutcome(symbol="E", model_rank=5, model_score=0.75, actual_multiplier=6.0),
        TokenOutcome(symbol="F", model_rank=6, model_score=0.70, actual_multiplier=1.5),
        TokenOutcome(symbol="G", model_rank=7, model_score=0.65, actual_multiplier=15.0),
        TokenOutcome(symbol="H", model_rank=8, model_score=0.60, actual_multiplier=0.3),
        TokenOutcome(symbol="I", model_rank=9, model_score=0.55, actual_multiplier=3.0),
        TokenOutcome(symbol="J", model_rank=10, model_score=0.50, actual_multiplier=20.0),
    ]


# ---------------------------------------------------------------------------
# TestTokenOutcome
# ---------------------------------------------------------------------------


class TestTokenOutcome:
    """Unit tests for the TokenOutcome dataclass."""

    def test_token_outcome_required_fields_are_set(self) -> None:
        """TokenOutcome must store symbol, model_rank, model_score, actual_multiplier."""
        o = TokenOutcome(symbol="BTC", model_rank=1, model_score=0.9, actual_multiplier=10.0)
        assert o.symbol == "BTC"
        assert o.model_rank == 1
        assert o.model_score == pytest.approx(0.9)
        assert o.actual_multiplier == pytest.approx(10.0)

    def test_token_outcome_is_winner_true_at_default_threshold(self) -> None:
        """is_winner() must return True when actual_multiplier >= 5.0 (default)."""
        o = TokenOutcome(symbol="SOL", model_rank=1, model_score=0.8, actual_multiplier=5.0)
        assert o.is_winner() is True

    def test_token_outcome_is_winner_false_below_threshold(self) -> None:
        """is_winner() must return False when actual_multiplier < 5.0."""
        o = TokenOutcome(symbol="XRP", model_rank=2, model_score=0.7, actual_multiplier=4.9)
        assert o.is_winner() is False

    def test_token_outcome_is_winner_custom_threshold(self) -> None:
        """is_winner(threshold) must use the provided multiplier threshold."""
        o = TokenOutcome(symbol="ETH", model_rank=1, model_score=0.9, actual_multiplier=3.0)
        assert o.is_winner(threshold=2.0) is True
        assert o.is_winner(threshold=5.0) is False

    def test_token_outcome_outperformed_market_true(self) -> None:
        """outperformed_market() must return True when multiplier > market_multiplier."""
        o = TokenOutcome(symbol="BTC", model_rank=1, model_score=0.9, actual_multiplier=3.0)
        assert o.outperformed_market(market_multiplier=2.0) is True

    def test_token_outcome_outperformed_market_false(self) -> None:
        """outperformed_market() must return False when multiplier <= market_multiplier."""
        o = TokenOutcome(symbol="DOGE", model_rank=5, model_score=0.5, actual_multiplier=1.0)
        assert o.outperformed_market(market_multiplier=2.0) is False


# ---------------------------------------------------------------------------
# TestPrecisionAtK
# ---------------------------------------------------------------------------


class TestPrecisionAtK:
    """Tests for compute_precision_at_k()."""

    def test_precision_at_5_with_known_outcomes(self) -> None:
        """Top 5 = [A(12x), B(2x), C(8x), D(0.5x), E(6x)] → 3 winners out of 5 → 0.6."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=5) == pytest.approx(0.6)

    def test_precision_at_3_with_known_outcomes(self) -> None:
        """Top 3 = [A(12x), B(2x), C(8x)] → 2 winners out of 3 → ~0.667."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=3) == pytest.approx(2.0 / 3.0)

    def test_precision_at_10_with_known_outcomes(self) -> None:
        """All 10 tokens: 5 winners out of 10 → 0.5."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=10) == pytest.approx(0.5)

    def test_precision_at_1_with_winner_at_top(self) -> None:
        """Top 1 = [A(12x)] → 1 winner → 1.0."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=1) == pytest.approx(1.0)

    def test_precision_at_k_empty_list_returns_zero(self) -> None:
        """compute_precision_at_k with no outcomes must return 0.0."""
        assert compute_precision_at_k([], k=5) == pytest.approx(0.0)

    def test_precision_at_k_with_custom_threshold(self) -> None:
        """Precision with threshold=10x: winners = A(12x), G(15x), J(20x).
        Top 5 = [A, B, C, D, E] → 1 winner (A) → 0.2."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=5, winner_threshold=10.0) == pytest.approx(0.2)

    def test_precision_at_k_larger_than_list_returns_full_precision(self) -> None:
        """When k > len(outcomes), use all available outcomes."""
        outcomes = _make_outcomes()
        assert compute_precision_at_k(outcomes, k=100) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# TestRecallAtK
# ---------------------------------------------------------------------------


class TestRecallAtK:
    """Tests for compute_recall_at_k()."""

    def test_recall_at_5_with_known_outcomes(self) -> None:
        """5 total winners. Top 5 has 3 winners → recall = 3/5 = 0.6."""
        outcomes = _make_outcomes()
        assert compute_recall_at_k(outcomes, k=5) == pytest.approx(0.6)

    def test_recall_at_10_returns_one(self) -> None:
        """All 10 tokens include all 5 winners → recall = 1.0."""
        outcomes = _make_outcomes()
        assert compute_recall_at_k(outcomes, k=10) == pytest.approx(1.0)

    def test_recall_at_1_with_one_winner(self) -> None:
        """Top 1 has 1 winner → recall = 1/5 = 0.2."""
        outcomes = _make_outcomes()
        assert compute_recall_at_k(outcomes, k=1) == pytest.approx(0.2)

    def test_recall_at_k_empty_list_returns_zero(self) -> None:
        """compute_recall_at_k with no outcomes must return 0.0."""
        assert compute_recall_at_k([], k=5) == pytest.approx(0.0)

    def test_recall_at_k_no_winners_returns_zero(self) -> None:
        """When no tokens are actual winners, recall must be 0.0."""
        outcomes = [
            TokenOutcome(symbol="X", model_rank=1, model_score=0.9, actual_multiplier=1.0),
            TokenOutcome(symbol="Y", model_rank=2, model_score=0.8, actual_multiplier=2.0),
        ]
        assert compute_recall_at_k(outcomes, k=2) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestHitRate
# ---------------------------------------------------------------------------


class TestHitRate:
    """Tests for compute_hit_rate()."""

    def test_hit_rate_top_5_with_market_2x(self) -> None:
        """Top 5: A(12x), B(2x), C(8x), D(0.5x), E(6x).
        Outperformers (>2x): A, C, E = 3 out of 5 → 0.6."""
        outcomes = _make_outcomes()
        assert compute_hit_rate(outcomes, k=5, market_multiplier=2.0) == pytest.approx(0.6)

    def test_hit_rate_top_3_with_market_1x(self) -> None:
        """Top 3: A(12x), B(2x), C(8x). All > 1x → 3/3 = 1.0."""
        outcomes = _make_outcomes()
        assert compute_hit_rate(outcomes, k=3, market_multiplier=1.0) == pytest.approx(1.0)

    def test_hit_rate_empty_list_returns_zero(self) -> None:
        """compute_hit_rate with no outcomes must return 0.0."""
        assert compute_hit_rate([], k=5, market_multiplier=2.0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestValidationReport
# ---------------------------------------------------------------------------


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_validation_report_fields_are_set(self) -> None:
        """ValidationReport must expose precision, recall, hit_rate and breakdown."""
        report = ValidationReport(
            precision_at_k=0.6,
            recall_at_k=0.6,
            hit_rate=0.5,
            k=10,
            winner_threshold=5.0,
            n_total_tokens=50,
            n_winners=10,
            token_breakdown=[],
        )
        assert report.precision_at_k == pytest.approx(0.6)
        assert report.recall_at_k == pytest.approx(0.6)
        assert report.hit_rate == pytest.approx(0.5)
        assert report.k == 10

    def test_validation_report_model_is_useful_true_when_precision_above_half(self) -> None:
        """model_is_useful must be True when precision_at_k > 0.5."""
        report = ValidationReport(
            precision_at_k=0.6,
            recall_at_k=0.5,
            hit_rate=0.5,
            k=10,
            winner_threshold=5.0,
            n_total_tokens=50,
            n_winners=10,
            token_breakdown=[],
        )
        assert report.model_is_useful is True

    def test_validation_report_model_is_useful_false_when_precision_below_half(self) -> None:
        """model_is_useful must be False when precision_at_k <= 0.5."""
        report = ValidationReport(
            precision_at_k=0.4,
            recall_at_k=0.5,
            hit_rate=0.5,
            k=10,
            winner_threshold=5.0,
            n_total_tokens=50,
            n_winners=10,
            token_breakdown=[],
        )
        assert report.model_is_useful is False


# ---------------------------------------------------------------------------
# TestGenerateValidationReport
# ---------------------------------------------------------------------------


class TestGenerateValidationReport:
    """Tests for generate_validation_report() — end-to-end metric computation."""

    def test_generate_report_returns_validation_report(self) -> None:
        """generate_validation_report must return a ValidationReport instance."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5, market_multiplier=2.0)
        assert isinstance(report, ValidationReport)

    def test_generate_report_precision_matches_compute(self) -> None:
        """precision_at_k in report must match compute_precision_at_k."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5)
        assert report.precision_at_k == pytest.approx(0.6)

    def test_generate_report_recall_matches_compute(self) -> None:
        """recall_at_k in report must match compute_recall_at_k."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5)
        assert report.recall_at_k == pytest.approx(0.6)

    def test_generate_report_hit_rate_matches_compute(self) -> None:
        """hit_rate in report must match compute_hit_rate."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5, market_multiplier=2.0)
        assert report.hit_rate == pytest.approx(0.6)

    def test_generate_report_token_breakdown_has_correct_length(self) -> None:
        """token_breakdown must contain min(k, len(outcomes)) entries."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5)
        assert len(report.token_breakdown) == 5

    def test_generate_report_counts_winners_correctly(self) -> None:
        """n_winners must be total winners in the full outcome set."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5)
        assert report.n_winners == 5  # A, C, E, G, J

    def test_generate_report_n_total_tokens_is_full_set(self) -> None:
        """n_total_tokens must equal len(outcomes)."""
        outcomes = _make_outcomes()
        report = generate_validation_report(outcomes, k=5)
        assert report.n_total_tokens == 10
