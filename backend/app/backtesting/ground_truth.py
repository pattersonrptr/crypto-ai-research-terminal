"""Ground truth computation for backtesting cycles.

Determines which tokens were actual winners in a given cycle by
computing the ROI multiplier (top price / bottom price) and
classifying each token into a performance tier.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PerformanceTier(Enum):
    """How well a token performed during a market cycle."""

    BIG_WINNER = "big_winner"
    WINNER = "winner"
    AVERAGE = "average"
    LOSER = "loser"


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def compute_roi(bottom_price: float, top_price: float) -> float:
    """Return the ROI multiplier (top / bottom).

    Returns 0.0 when bottom_price is <= 0.
    """
    if bottom_price <= 0:
        return 0.0
    return top_price / bottom_price


def classify_performance(
    roi: float,
    *,
    winner_threshold: float = 5.0,
    big_winner_threshold: float = 10.0,
) -> PerformanceTier:
    """Classify a token's ROI into a performance tier.

    Default thresholds:
        >= 10x  → BIG_WINNER
        >= 5x   → WINNER
        > 1x    → AVERAGE
        <= 1x   → LOSER
    """
    if roi >= big_winner_threshold:
        return PerformanceTier.BIG_WINNER
    if roi >= winner_threshold:
        return PerformanceTier.WINNER
    if roi > 1.0:
        return PerformanceTier.AVERAGE
    return PerformanceTier.LOSER


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GroundTruthEntry:
    """Performance data for a single token in a cycle."""

    symbol: str
    bottom_price: float
    top_price: float
    roi_multiplier: float
    tier: PerformanceTier

    @property
    def is_winner(self) -> bool:
        """True when the token is at least a WINNER (includes BIG_WINNER)."""
        return self.tier in (PerformanceTier.WINNER, PerformanceTier.BIG_WINNER)


@dataclass(frozen=True, slots=True)
class CycleGroundTruth:
    """Ground truth for all tokens in a single cycle."""

    cycle_name: str
    entries: list[GroundTruthEntry]

    @property
    def winners(self) -> list[GroundTruthEntry]:
        """Return entries that are at least WINNER tier."""
        return [e for e in self.entries if e.is_winner]

    @property
    def n_winners(self) -> int:
        """Number of winner tokens."""
        return len(self.winners)

    @property
    def winner_symbols(self) -> set[str]:
        """Set of symbols that are winners."""
        return {e.symbol for e in self.winners}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_ground_truth(
    cycle_name: str,
    bottom_prices: dict[str, float],
    top_prices: dict[str, float],
    *,
    winner_threshold: float = 5.0,
    big_winner_threshold: float = 10.0,
) -> CycleGroundTruth:
    """Build ground truth from bottom and top price dictionaries.

    Tokens that only exist in ``bottom_prices`` or only in
    ``top_prices`` are silently excluded.  Tokens with a bottom
    price of zero are also excluded.

    Entries are returned **sorted by ROI descending**.
    """
    entries: list[GroundTruthEntry] = []
    for symbol, bottom in bottom_prices.items():
        top = top_prices.get(symbol)
        if top is None or bottom <= 0:
            continue
        roi = compute_roi(bottom, top)
        tier = classify_performance(
            roi,
            winner_threshold=winner_threshold,
            big_winner_threshold=big_winner_threshold,
        )
        entries.append(
            GroundTruthEntry(
                symbol=symbol,
                bottom_price=bottom,
                top_price=top,
                roi_multiplier=roi,
                tier=tier,
            )
        )

    entries.sort(key=lambda e: e.roi_multiplier, reverse=True)
    return CycleGroundTruth(cycle_name=cycle_name, entries=entries)
