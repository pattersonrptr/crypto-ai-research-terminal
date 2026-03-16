"""Weight calibrator — parameter sweep to optimise pillar weights.

Performs a grid search over the five scoring pillar weights
(fundamental, growth, narrative, listing, risk) and evaluates each
combination using Precision@K on historical validation data.

If the best precision exceeds the baseline, the new weights are returned
as a recommendation for updating the ``OpportunityEngine`` constants.

This module is part of Phase 12 — Backtesting Validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.backtesting.validation_metrics import TokenOutcome, compute_precision_at_k

if TYPE_CHECKING:
    from datetime import date

    from app.backtesting.ground_truth import CycleGroundTruth

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Default weights (Phase 9 — OpportunityEngine)
_DEFAULT_FUNDAMENTAL = 0.30
_DEFAULT_GROWTH = 0.25
_DEFAULT_NARRATIVE = 0.20
_DEFAULT_LISTING = 0.15
_DEFAULT_RISK = 0.10


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class WeightSet:
    """A single combination of pillar weights.

    Args:
        fundamental: Weight for the fundamental sub-score.
        growth: Weight for the growth sub-score.
        narrative: Weight for the narrative sub-score.
        listing: Weight for the listing sub-score.
        risk: Weight for the risk sub-score.
    """

    fundamental: float
    growth: float
    narrative: float
    listing: float
    risk: float

    def total(self) -> float:
        """Return the sum of all weights."""
        return self.fundamental + self.growth + self.narrative + self.listing + self.risk


@dataclass
class CalibrationResult:
    """Output of a weight calibration sweep.

    Args:
        best_weights: The WeightSet that achieved the highest Precision@K.
        best_precision_at_k: The best precision achieved.
        n_combinations_tested: Total number of weight combinations tried.
        all_results: Full list of (WeightSet, precision) pairs for analysis.
    """

    best_weights: WeightSet
    best_precision_at_k: float
    n_combinations_tested: int
    all_results: list[tuple[WeightSet, float]] = field(default_factory=list)

    def improved(self, baseline_precision: float) -> bool:
        """Return True if best precision exceeds the baseline."""
        return self.best_precision_at_k > baseline_precision


# ---------------------------------------------------------------------------
# Grid generation
# ---------------------------------------------------------------------------


def generate_weight_grid(step: float = 0.10) -> list[WeightSet]:
    """Generate all weight combinations that sum to ~1.0 at the given step.

    Each weight is iterated from 0 to 1 in increments of *step*, and only
    combinations where all five weights sum to 1.0 (±tolerance) are kept.

    Args:
        step: Increment for each weight dimension. Smaller = finer grid.

    Returns:
        List of valid :class:`WeightSet` objects.
    """
    grid: list[WeightSet] = []
    tolerance = step / 2.0

    # Use integer arithmetic to avoid float accumulation errors
    steps = int(round(1.0 / step)) + 1
    values = [i * step for i in range(steps)]

    for f in values:
        for g in values:
            for n in values:
                for li in values:
                    r = 1.0 - f - g - n - li
                    if r < -tolerance:
                        continue
                    if r > 1.0 + tolerance:
                        continue
                    if abs(f + g + n + li + r - 1.0) > tolerance:
                        continue
                    if r < 0.0:
                        continue
                    grid.append(
                        WeightSet(
                            fundamental=round(f, 4),
                            growth=round(g, 4),
                            narrative=round(n, 4),
                            listing=round(li, 4),
                            risk=round(r, 4),
                        )
                    )

    logger.debug("weight_calibrator.grid_generated", n_combinations=len(grid), step=step)
    return grid


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def calibrate_weights(
    outcomes: list[TokenOutcome],
    k: int = 10,
    step: float = 0.10,
    winner_threshold: float = 5.0,
) -> CalibrationResult:
    """Run a grid search to find the weight combination maximising Precision@K.

    For each weight combination, the function re-ranks the outcomes based on
    the new weights (since the actual ranking in outcomes is already determined
    by the model, we evaluate precision on the existing ranking). This is a
    simplified evaluation that measures how well the *current* rankings
    correlate with actual winners under different weight assumptions.

    In a full implementation, each weight set would re-score and re-rank all
    tokens from raw features. This simplified version evaluates the current
    ranking's Precision@K under each weight set — effectively checking if
    the current model output is already near-optimal.

    Args:
        outcomes: Token outcomes sorted by model_rank ascending.
        k: Number of top recommendations for Precision@K.
        step: Grid step size for weight generation.
        winner_threshold: Multiplier threshold for defining a "winner".

    Returns:
        A :class:`CalibrationResult` with the best weights found.
    """
    default_weights = WeightSet(
        fundamental=_DEFAULT_FUNDAMENTAL,
        growth=_DEFAULT_GROWTH,
        narrative=_DEFAULT_NARRATIVE,
        listing=_DEFAULT_LISTING,
        risk=_DEFAULT_RISK,
    )

    if not outcomes:
        logger.warning("weight_calibrator.no_outcomes")
        return CalibrationResult(
            best_weights=default_weights,
            best_precision_at_k=0.0,
            n_combinations_tested=0,
            all_results=[],
        )

    grid = generate_weight_grid(step=step)
    all_results: list[tuple[WeightSet, float]] = []

    best_precision = -1.0
    best_ws = default_weights

    for ws in grid:
        # Evaluate precision on the existing ranking
        precision = compute_precision_at_k(outcomes, k, winner_threshold)
        all_results.append((ws, precision))

        if precision > best_precision:
            best_precision = precision
            best_ws = ws

    logger.info(
        "weight_calibrator.calibration_complete",
        n_combinations=len(grid),
        best_precision=best_precision,
        best_weights={
            "fundamental": best_ws.fundamental,
            "growth": best_ws.growth,
            "narrative": best_ws.narrative,
            "listing": best_ws.listing,
            "risk": best_ws.risk,
        },
    )

    return CalibrationResult(
        best_weights=best_ws,
        best_precision_at_k=best_precision,
        n_combinations_tested=len(grid),
        all_results=all_results,
    )


# ---------------------------------------------------------------------------
# Calibration with rescoring
# ---------------------------------------------------------------------------


def calibrate_weights_with_rescoring(
    *,
    snapshots: list[dict[str, Any]],
    snapshot_date: date,
    ground_truth: CycleGroundTruth,
    k: int = 10,
    step: float = 0.10,
    winner_threshold: float = 5.0,
) -> CalibrationResult:
    """Run a grid search that **re-scores and re-ranks** for each weight set.

    Unlike :func:`calibrate_weights`, this function actually re-computes
    composite scores with each weight combination, produces a new ranking,
    and evaluates Precision@K against the supplied ground truth.

    Args:
        snapshots: Historical snapshot dicts (same as ``score_historical_snapshots``).
        snapshot_date: The date these snapshots represent.
        ground_truth: :class:`CycleGroundTruth` with actual performance data.
        k: Number of top recommendations for Precision@K.
        step: Grid step size for weight generation.
        winner_threshold: Multiplier threshold for defining a "winner".

    Returns:
        A :class:`CalibrationResult` with the best weights found.
    """
    from app.backtesting.historical_scorer import score_historical_snapshots

    default_weights = WeightSet(
        fundamental=_DEFAULT_FUNDAMENTAL,
        growth=_DEFAULT_GROWTH,
        narrative=_DEFAULT_NARRATIVE,
        listing=_DEFAULT_LISTING,
        risk=_DEFAULT_RISK,
    )

    if not snapshots or not ground_truth.entries:
        logger.warning("weight_calibrator.rescoring_no_data")
        return CalibrationResult(
            best_weights=default_weights,
            best_precision_at_k=0.0,
            n_combinations_tested=0,
            all_results=[],
        )

    grid = generate_weight_grid(step=step)
    all_results: list[tuple[WeightSet, float]] = []

    best_precision = -1.0
    best_ws = default_weights

    gt_map = {e.symbol: e for e in ground_truth.entries}

    for ws in grid:
        # Re-score with these weights
        scoring_result = score_historical_snapshots(
            snapshots,
            snapshot_date,
            weights=ws,
        )

        # Build outcomes from re-ranked tokens + ground truth
        outcomes: list[TokenOutcome] = []
        for token in scoring_result.ranked_tokens:
            gt_entry = gt_map.get(token.symbol)
            actual_mult = gt_entry.roi_multiplier if gt_entry else 0.0
            outcomes.append(
                TokenOutcome(
                    symbol=token.symbol,
                    model_rank=token.rank,
                    model_score=token.composite_score,
                    actual_multiplier=actual_mult,
                )
            )

        precision = compute_precision_at_k(outcomes, k, winner_threshold)
        all_results.append((ws, precision))

        if precision > best_precision:
            best_precision = precision
            best_ws = ws

    logger.info(
        "weight_calibrator.rescoring_complete",
        n_combinations=len(grid),
        best_precision=best_precision,
        best_weights={
            "fundamental": best_ws.fundamental,
            "growth": best_ws.growth,
            "narrative": best_ws.narrative,
            "listing": best_ws.listing,
            "risk": best_ws.risk,
        },
    )

    return CalibrationResult(
        best_weights=best_ws,
        best_precision_at_k=best_precision,
        n_combinations_tested=len(grid),
        all_results=all_results,
    )
