"""WhaleTracker — tracks whale wallet activity and concentration.

Monitors:
- Top wallet concentration (top 10/50 wallets)
- Accumulation/distribution patterns
- Large transaction detection (>5% of supply movements)
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class WhaleAnalysisResult:
    """Result of whale activity analysis."""

    concentration_risk: float  # 0.0 (decentralized) to 1.0 (highly concentrated)

    # Concentration metrics
    top10_concentration: float  # Fraction held by top 10 wallets
    top50_concentration: float  # Fraction held by top 50 wallets

    # Activity signals (0.0 to 1.0)
    accumulation_signal: float  # Net buying by whales
    distribution_signal: float  # Net selling by whales

    # Flags
    large_movements_detected: bool  # Any single move > 5% of supply


# Thresholds
_LARGE_MOVEMENT_THRESHOLD = 0.05  # 5% of supply
_HIGH_CONCENTRATION_THRESHOLD = 0.50  # 50% in top 10 is concerning

_REQUIRED_FIELDS = {
    "wallet_balances",
    "total_supply",
    "balance_changes_24h",
}


class WhaleTracker:
    """Analyzes whale wallet holdings and activity patterns."""

    @staticmethod
    def _calculate_concentration(balances: list[float], total_supply: float, top_n: int) -> float:
        """Calculate what fraction of supply is held by top N wallets."""
        if total_supply <= 0:
            return 0.0

        sorted_balances = sorted(balances, reverse=True)
        top_sum = sum(sorted_balances[:top_n])
        return min(top_sum / total_supply, 1.0)

    @staticmethod
    def _calculate_accumulation_distribution(
        changes: list[float], total_supply: float
    ) -> tuple[float, float]:
        """Calculate accumulation and distribution signals.

        Returns:
            Tuple of (accumulation_signal, distribution_signal) in [0, 1].
        """
        if total_supply <= 0:
            return 0.0, 0.0

        net_change = sum(changes)
        change_magnitude = abs(net_change) / total_supply

        # Scale to 0-1 range (10% net change = signal of 1.0)
        signal_strength = min(change_magnitude / 0.10, 1.0)

        if net_change > 0:
            return signal_strength, 0.0
        elif net_change < 0:
            return 0.0, signal_strength
        return 0.0, 0.0

    @staticmethod
    def _detect_large_movements(changes: list[float], total_supply: float) -> bool:
        """Detect if any single wallet moved > threshold of supply."""
        if total_supply <= 0:
            return False

        return any(abs(change) / total_supply >= _LARGE_MOVEMENT_THRESHOLD for change in changes)

    @classmethod
    def analyze(cls, data: dict[str, Any]) -> WhaleAnalysisResult:
        """Analyze whale wallet data for concentration and activity.

        Args:
            data: Dict containing:
                - wallet_balances: list[float] — current balances of top wallets
                - total_supply: float — total token supply
                - balance_changes_24h: list[float] — 24h balance changes per wallet

        Returns:
            WhaleAnalysisResult with concentration metrics and signals.

        Raises:
            ScoringError: If required fields are missing or invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"WhaleTracker: missing fields {missing}")

        balances = data["wallet_balances"]
        total_supply = data["total_supply"]
        changes = data["balance_changes_24h"]

        # Validate values
        if len(balances) == 0:
            raise ScoringError("WhaleTracker: wallet_balances cannot be empty")
        if total_supply <= 0:
            raise ScoringError(f"WhaleTracker: total_supply must be > 0, got {total_supply}")
        if len(balances) != len(changes):
            raise ScoringError(
                f"WhaleTracker: wallet_balances and balance_changes_24h must have "
                f"same length ({len(balances)} != {len(changes)})"
            )

        # Calculate metrics
        top10_conc = cls._calculate_concentration(balances, total_supply, 10)
        top50_conc = cls._calculate_concentration(balances, total_supply, 50)
        accum, distrib = cls._calculate_accumulation_distribution(changes, total_supply)
        large_moves = cls._detect_large_movements(changes, total_supply)

        # Concentration risk based on top 10 holdings
        # 50% or more in top 10 = high risk
        concentration_risk = min(top10_conc / _HIGH_CONCENTRATION_THRESHOLD, 1.0)

        return WhaleAnalysisResult(
            concentration_risk=concentration_risk,
            top10_concentration=top10_conc,
            top50_concentration=top50_conc,
            accumulation_signal=accum,
            distribution_signal=distrib,
            large_movements_detected=large_moves,
        )
