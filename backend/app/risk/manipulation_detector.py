"""ManipulationDetector — detects market manipulation patterns.

Evaluates three manipulation indicators:
- Pump & dump: rapid price spike (>50%) followed by crash (>30%)
- Wash trading: low unique traders ratio (<30%)
- Coordinated social: many posts in short time window
"""

from dataclasses import dataclass
from typing import Any

from app.exceptions import ScoringError


@dataclass(frozen=True)
class ManipulationRiskResult:
    """Result of manipulation risk analysis."""

    risk_score: float  # 0.0 (clean) to 1.0 (highly suspicious)

    # Individual manipulation flags
    pump_dump_detected: bool
    wash_trading_detected: bool
    coordinated_social_detected: bool

    # Metrics for transparency
    max_price_spike_pct: float
    max_price_drop_pct: float
    social_burst_count: int


# Thresholds for detection
_PUMP_SPIKE_THRESHOLD = 0.50  # 50% price increase
_DUMP_DROP_THRESHOLD = 0.30  # 30% price drop from peak
_WASH_TRADING_THRESHOLD = 0.30  # < 30% unique traders
_SOCIAL_BURST_WINDOW = 60.0  # 60 seconds
_SOCIAL_BURST_MIN_COUNT = 8  # minimum posts in window to flag

# Weights for risk score (sum to 1.0)
_WEIGHTS = {
    "pump_dump": 0.40,
    "wash_trading": 0.35,
    "coordinated_social": 0.25,
}

_REQUIRED_FIELDS = {
    "price_history",
    "volume_history",
    "social_post_times",
    "unique_traders_ratio",
}


class ManipulationDetector:
    """Analyzes market data for manipulation patterns."""

    @staticmethod
    def _detect_pump_dump(prices: list[float]) -> tuple[bool, float, float]:
        """Detect pump and dump pattern in price history.

        Returns:
            Tuple of (detected, max_spike_pct, max_drop_pct).
        """
        if len(prices) < 3:
            return False, 0.0, 0.0

        min_price = prices[0]
        max_price = prices[0]
        max_spike_pct = 0.0
        max_drop_pct = 0.0

        # Track the pump phase
        for price in prices:
            if price < min_price:
                min_price = price
            if price > max_price:
                max_price = price

            # Calculate spike from minimum
            if min_price > 0:
                spike = (price - min_price) / min_price
                max_spike_pct = max(max_spike_pct, spike)

        # Track the dump phase (drop from maximum)
        for price in prices:
            if max_price > 0:
                drop = (max_price - price) / max_price
                max_drop_pct = max(max_drop_pct, drop)

        detected = max_spike_pct >= _PUMP_SPIKE_THRESHOLD and max_drop_pct >= _DUMP_DROP_THRESHOLD

        return detected, max_spike_pct, max_drop_pct

    @staticmethod
    def _detect_wash_trading(unique_ratio: float) -> bool:
        """Detect wash trading based on unique traders ratio."""
        return unique_ratio < _WASH_TRADING_THRESHOLD

    @staticmethod
    def _detect_coordinated_social(post_times: list[float]) -> tuple[bool, int]:
        """Detect coordinated social activity via burst detection.

        Args:
            post_times: List of post timestamps (in seconds).

        Returns:
            Tuple of (detected, max_burst_count).
        """
        if len(post_times) < _SOCIAL_BURST_MIN_COUNT:
            return False, 0

        sorted_times = sorted(post_times)
        max_burst = 0

        # Sliding window to find burst
        for i, start_time in enumerate(sorted_times):
            end_time = start_time + _SOCIAL_BURST_WINDOW
            count = sum(1 for t in sorted_times[i:] if t <= end_time)
            max_burst = max(max_burst, count)

        detected = max_burst >= _SOCIAL_BURST_MIN_COUNT
        return detected, max_burst

    @classmethod
    def analyze(cls, data: dict[str, Any]) -> ManipulationRiskResult:
        """Analyze market data for manipulation patterns.

        Args:
            data: Dict containing:
                - price_history: list[float] — historical prices
                - volume_history: list[float] — historical volumes
                - social_post_times: list[float] — timestamps of social posts
                - unique_traders_ratio: float — fraction of unique traders (0-1)

        Returns:
            ManipulationRiskResult with risk_score and detection flags.

        Raises:
            ScoringError: If required fields are missing or invalid.
        """
        # Validate required fields
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ScoringError(f"ManipulationDetector: missing fields {missing}")

        prices = data["price_history"]
        unique_ratio = data["unique_traders_ratio"]
        post_times = data["social_post_times"]

        # Validate values
        if len(prices) < 2:
            raise ScoringError(
                "ManipulationDetector: price_history must have at least 2 data points"
            )
        if not 0.0 <= unique_ratio <= 1.0:
            raise ScoringError(
                f"ManipulationDetector: unique_traders_ratio must be in [0, 1], got {unique_ratio}"
            )

        # Detect patterns
        pump_dump, spike_pct, drop_pct = cls._detect_pump_dump(prices)
        wash_trading = cls._detect_wash_trading(unique_ratio)
        coord_social, burst_count = cls._detect_coordinated_social(post_times)

        # Calculate component risks (0.0-1.0 each)
        pump_dump_risk = 1.0 if pump_dump else max(spike_pct / _PUMP_SPIKE_THRESHOLD, 0.0) * 0.5
        wash_risk = (
            1.0
            if wash_trading
            else max(0.0, (_WASH_TRADING_THRESHOLD - unique_ratio) / _WASH_TRADING_THRESHOLD)
        )
        social_risk = 1.0 if coord_social else 0.0

        # Weighted composite
        risk_score = (
            _WEIGHTS["pump_dump"] * pump_dump_risk
            + _WEIGHTS["wash_trading"] * wash_risk
            + _WEIGHTS["coordinated_social"] * social_risk
        )

        return ManipulationRiskResult(
            risk_score=min(risk_score, 1.0),
            pump_dump_detected=pump_dump,
            wash_trading_detected=wash_trading,
            coordinated_social_detected=coord_social,
            max_price_spike_pct=spike_pct,
            max_price_drop_pct=drop_pct,
            social_burst_count=burst_count,
        )
