"""Validation metrics — measures predictive accuracy of the scoring model.

Compares the model's ranked token recommendations against actual price
performance in a subsequent market cycle.  Key metrics:

- **Precision@K**: Of the top-K recommended tokens, how many were actual
  winners (achieved >= threshold multiplier)?
- **Recall@K**: Of all actual winners, how many appeared in the top-K?
- **Hit rate**: Fraction of top-K tokens that outperformed the overall market.

This module is part of Phase 12 — Backtesting Validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

logger: structlog.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_WINNER_THRESHOLD: float = 5.0
_DEFAULT_MARKET_MULTIPLIER: float = 2.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TokenOutcome:
    """Outcome of a single token: model's prediction vs. actual performance.

    Args:
        symbol: Token ticker (e.g. ``"SOL"``).
        model_rank: Rank assigned by the scoring model (1 = highest).
        model_score: Composite opportunity score in [0, 1].
        actual_multiplier: Actual price multiplier from snapshot date
            to the cycle peak (e.g. 10.0 means the price went 10×).
    """

    symbol: str
    model_rank: int
    model_score: float
    actual_multiplier: float

    def is_winner(self, threshold: float = _DEFAULT_WINNER_THRESHOLD) -> bool:
        """Return True if this token achieved >= *threshold* price multiplier."""
        return self.actual_multiplier >= threshold

    def outperformed_market(self, market_multiplier: float = _DEFAULT_MARKET_MULTIPLIER) -> bool:
        """Return True if this token outperformed the overall market."""
        return self.actual_multiplier > market_multiplier


@dataclass
class ValidationReport:
    """Summary of backtesting validation metrics.

    Args:
        precision_at_k: Fraction of top-K recommended that were actual winners.
        recall_at_k: Fraction of all actual winners that appeared in top-K.
        hit_rate: Fraction of top-K that outperformed the market.
        k: The K value used for top-K metrics.
        winner_threshold: Multiplier threshold used to define a "winner".
        n_total_tokens: Total number of tokens evaluated.
        n_winners: Number of actual winners in the full dataset.
        token_breakdown: Per-token detail for the top-K recommendations.
    """

    precision_at_k: float
    recall_at_k: float
    hit_rate: float
    k: int
    winner_threshold: float
    n_total_tokens: int
    n_winners: int
    token_breakdown: list[TokenOutcome] = field(default_factory=list)

    @property
    def model_is_useful(self) -> bool:
        """Return True when precision exceeds 50% — model beats random."""
        return self.precision_at_k > 0.5


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------


def compute_precision_at_k(
    outcomes: list[TokenOutcome],
    k: int,
    winner_threshold: float = _DEFAULT_WINNER_THRESHOLD,
) -> float:
    """Compute Precision@K: fraction of top-K that are actual winners.

    Args:
        outcomes: Token outcomes sorted by model_rank ascending.
        k: Number of top recommendations to evaluate.
        winner_threshold: Multiplier threshold defining a "winner".

    Returns:
        Precision in [0.0, 1.0]. Returns 0.0 when the list is empty.
    """
    if not outcomes:
        return 0.0

    top_k = outcomes[: min(k, len(outcomes))]
    n_winners = sum(1 for o in top_k if o.is_winner(threshold=winner_threshold))
    precision = n_winners / len(top_k)

    logger.debug(
        "validation.precision_at_k",
        k=k,
        n_winners_in_top_k=n_winners,
        precision=precision,
    )
    return precision


def compute_recall_at_k(
    outcomes: list[TokenOutcome],
    k: int,
    winner_threshold: float = _DEFAULT_WINNER_THRESHOLD,
) -> float:
    """Compute Recall@K: fraction of all winners that are in the top-K.

    Args:
        outcomes: Token outcomes sorted by model_rank ascending.
        k: Number of top recommendations to evaluate.
        winner_threshold: Multiplier threshold defining a "winner".

    Returns:
        Recall in [0.0, 1.0]. Returns 0.0 when there are no winners
        or the list is empty.
    """
    if not outcomes:
        return 0.0

    total_winners = sum(1 for o in outcomes if o.is_winner(threshold=winner_threshold))
    if total_winners == 0:
        return 0.0

    top_k = outcomes[: min(k, len(outcomes))]
    winners_in_top_k = sum(1 for o in top_k if o.is_winner(threshold=winner_threshold))
    recall = winners_in_top_k / total_winners

    logger.debug(
        "validation.recall_at_k",
        k=k,
        total_winners=total_winners,
        winners_in_top_k=winners_in_top_k,
        recall=recall,
    )
    return recall


def compute_hit_rate(
    outcomes: list[TokenOutcome],
    k: int,
    market_multiplier: float = _DEFAULT_MARKET_MULTIPLIER,
) -> float:
    """Compute hit rate: fraction of top-K that outperformed the market.

    Args:
        outcomes: Token outcomes sorted by model_rank ascending.
        k: Number of top recommendations to evaluate.
        market_multiplier: Market benchmark multiplier.

    Returns:
        Hit rate in [0.0, 1.0]. Returns 0.0 when the list is empty.
    """
    if not outcomes:
        return 0.0

    top_k = outcomes[: min(k, len(outcomes))]
    n_outperformers = sum(1 for o in top_k if o.outperformed_market(market_multiplier))
    hit_rate = n_outperformers / len(top_k)

    logger.debug(
        "validation.hit_rate",
        k=k,
        n_outperformers=n_outperformers,
        hit_rate=hit_rate,
    )
    return hit_rate


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_validation_report(
    outcomes: list[TokenOutcome],
    k: int = 10,
    winner_threshold: float = _DEFAULT_WINNER_THRESHOLD,
    market_multiplier: float = _DEFAULT_MARKET_MULTIPLIER,
) -> ValidationReport:
    """Generate a full validation report from token outcomes.

    Args:
        outcomes: Token outcomes sorted by model_rank ascending.
        k: Number of top recommendations to evaluate.
        winner_threshold: Multiplier threshold for "winner" status.
        market_multiplier: Market benchmark multiplier for hit rate.

    Returns:
        A fully populated :class:`ValidationReport`.
    """
    precision = compute_precision_at_k(outcomes, k, winner_threshold)
    recall = compute_recall_at_k(outcomes, k, winner_threshold)
    hit_rate = compute_hit_rate(outcomes, k, market_multiplier)

    n_winners = sum(1 for o in outcomes if o.is_winner(threshold=winner_threshold))
    top_k = outcomes[: min(k, len(outcomes))]

    report = ValidationReport(
        precision_at_k=precision,
        recall_at_k=recall,
        hit_rate=hit_rate,
        k=k,
        winner_threshold=winner_threshold,
        n_total_tokens=len(outcomes),
        n_winners=n_winners,
        token_breakdown=top_k,
    )

    logger.info(
        "validation.report_generated",
        k=k,
        precision=precision,
        recall=recall,
        hit_rate=hit_rate,
        n_total=len(outcomes),
        n_winners=n_winners,
        model_is_useful=report.model_is_useful,
    )
    return report
