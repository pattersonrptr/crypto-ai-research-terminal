"""Historical scorer — runs the scoring pipeline on historical snapshots.

Takes a list of token state dictionaries (matching :class:`HistoricalSnapshot`
columns) for a given date and produces a ranked list of scored tokens.

The scorer applies a simplified version of the full scoring pipeline using
only the data available in historical snapshots: market cap, volume, price
and supply metrics.  Dev activity and social data are not available for
historical periods, so those pillars default to 0.5 (neutral).

This module is part of Phase 12 — Backtesting Validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.processors.normalizer import clamp, min_max_normalize

if TYPE_CHECKING:
    from datetime import date

    from app.backtesting.weight_calibrator import WeightSet

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# Normalisation bounds (same heuristics as FundamentalScorer)
_VOLUME_MCAP_MAX = 1.0
_MCAP_MAX = 1_000_000_000_000.0  # ~$1 T

# Default neutral values for unavailable pillars
_NEUTRAL_SCORE = 0.5


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class HistoricalScoredToken:
    """A single token scored on a historical snapshot date.

    Args:
        symbol: Token ticker.
        rank: Rank in the scored list (1 = highest score).
        composite_score: Final composite score in [0, 1].
        fundamental_score: Fundamental sub-score in [0, 1].
        growth_score: Growth sub-score in [0, 1].
        narrative_score: Narrative sub-score in [0, 1].
        listing_score: Listing sub-score in [0, 1].
        risk_score: Risk sub-score in [0, 1].
        volume_mcap_ratio: Volume / market-cap ratio used for scoring.
    """

    symbol: str
    rank: int
    composite_score: float
    fundamental_score: float
    growth_score: float = _NEUTRAL_SCORE
    narrative_score: float = _NEUTRAL_SCORE
    listing_score: float = _NEUTRAL_SCORE
    risk_score: float = _NEUTRAL_SCORE
    volume_mcap_ratio: float = 0.0


@dataclass
class HistoricalScoringResult:
    """Output of scoring a set of historical snapshots.

    Args:
        snapshot_date: The date these snapshots represent.
        ranked_tokens: Tokens sorted by composite_score descending.
    """

    snapshot_date: date
    ranked_tokens: list[HistoricalScoredToken] = field(default_factory=list)

    def top_k(self, k: int) -> list[HistoricalScoredToken]:
        """Return the top-K tokens by rank."""
        return self.ranked_tokens[:k]


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------


def _compute_fundamental_score(snapshot: dict[str, Any]) -> float:
    """Compute a fundamental score from a snapshot dict.

    Uses volume/mcap ratio and inverse market cap as primary signals.
    Tokens with smaller market caps and higher relative volume get
    higher scores — they represent higher-opportunity situations.

    Args:
        snapshot: Dict with keys matching HistoricalSnapshot columns.

    Returns:
        Fundamental score in [0.0, 1.0].
    """
    market_cap = float(snapshot.get("market_cap_usd", 0) or 0)
    volume = float(snapshot.get("volume_usd", 0) or 0)

    if market_cap <= 0:
        return 0.0

    vol_mcap_ratio = min(volume / market_cap, _VOLUME_MCAP_MAX)
    vol_norm = min_max_normalize(vol_mcap_ratio, 0.0, _VOLUME_MCAP_MAX)

    # Inverse market cap: smaller cap = more opportunity
    mcap_norm = min_max_normalize(market_cap, 0.0, _MCAP_MAX)
    inv_mcap = 1.0 - mcap_norm  # smaller mcap → higher score

    # Weighted: 60% volume ratio, 40% inverse mcap
    score = 0.60 * vol_norm + 0.40 * inv_mcap
    return clamp(score, 0.0, 1.0)


def score_historical_snapshots(
    snapshots: list[dict[str, Any]],
    snapshot_date: date,
    *,
    weights: WeightSet | None = None,
) -> HistoricalScoringResult:
    """Score a batch of historical snapshots and return ranked results.

    The scoring uses a simplified pipeline with only market-data-derived
    features (volume/mcap, inverse mcap).  Pillars requiring dev/social data
    are set to a neutral 0.5 default.

    When *weights* is provided the composite score uses those pillar weights
    instead of the hardcoded Phase 9 defaults.  This allows the weight
    calibrator to re-rank tokens under different weight assumptions.

    Args:
        snapshots: List of dicts with keys matching HistoricalSnapshot columns.
        snapshot_date: The date these snapshots represent.
        weights: Optional :class:`WeightSet` to override default pillar weights.

    Returns:
        A :class:`HistoricalScoringResult` with tokens ranked by score.
    """
    if not snapshots:
        return HistoricalScoringResult(snapshot_date=snapshot_date, ranked_tokens=[])

    # Resolve weights — default to Phase 9 values when not provided
    if weights is not None:
        w_fund = weights.fundamental
        w_growth = weights.growth
        w_narrative = weights.narrative
        w_listing = weights.listing
        w_risk = weights.risk
    else:
        # Rebalanced defaults — risk-heavy distribution
        w_fund = 0.25
        w_growth = 0.20
        w_narrative = 0.15
        w_listing = 0.10
        w_risk = 0.30

    scored: list[HistoricalScoredToken] = []

    for snap in snapshots:
        fund_score = _compute_fundamental_score(snap)
        market_cap = float(snap.get("market_cap_usd", 0) or 0)
        volume = float(snap.get("volume_usd", 0) or 0)
        vol_mcap = volume / market_cap if market_cap > 0 else 0.0

        composite = (
            w_fund * fund_score
            + w_growth * _NEUTRAL_SCORE
            + w_narrative * _NEUTRAL_SCORE
            + w_listing * _NEUTRAL_SCORE
            + w_risk * _NEUTRAL_SCORE
        )
        composite = clamp(composite, 0.0, 1.0)

        scored.append(
            HistoricalScoredToken(
                symbol=str(snap.get("symbol", "")),
                rank=0,  # assigned below
                composite_score=composite,
                fundamental_score=fund_score,
                growth_score=_NEUTRAL_SCORE,
                narrative_score=_NEUTRAL_SCORE,
                listing_score=_NEUTRAL_SCORE,
                risk_score=_NEUTRAL_SCORE,
                volume_mcap_ratio=vol_mcap,
            )
        )

    # Sort descending by composite score, then assign ranks
    scored.sort(key=lambda t: t.composite_score, reverse=True)
    for idx, token in enumerate(scored):
        token.rank = idx + 1

    logger.info(
        "historical_scorer.scored",
        snapshot_date=snapshot_date.isoformat(),
        n_tokens=len(scored),
        top_symbol=scored[0].symbol if scored else None,
    )

    return HistoricalScoringResult(
        snapshot_date=snapshot_date,
        ranked_tokens=scored,
    )
