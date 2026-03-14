"""Feature builder — constructs a normalised feature vector for ML models.

Transforms raw token data (market, dev, social, scores) into a fixed-length
numeric vector suitable for training and inference with scikit-learn / XGBoost.

Design decisions:
- All features are floats; missing optional data defaults to 0.0 (not NaN).
- Log1p is applied to heavily skewed counts (market cap, commits, stars, etc.)
  so the model is not dominated by outliers.
- ``FeatureVector`` is a dataclass so callers can access individual features
  by name while ``to_list()`` / ``feature_names()`` give ordered access for
  the sklearn/XGBoost array interface.
- ``RawTokenData`` is a plain dataclass — no DB dependency — so it can be
  constructed from ORM results, API responses, or test fixtures alike.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, fields


@dataclass
class RawTokenData:
    """Input bag for all signal sources available for a single token.

    Required fields are the minimum needed to compute basic market features.
    All other fields are optional and default to None when unavailable.
    """

    # --- Required market fields ------------------------------------------
    symbol: str
    market_cap_usd: float
    volume_24h_usd: float
    price_usd: float
    ath_usd: float

    # --- Optional market / circulating supply ----------------------------
    circulating_supply: float | None = None

    # --- Optional dev activity -------------------------------------------
    commits_30d: int | None = None
    contributors: int | None = None
    stars: int | None = None
    forks: int | None = None

    # --- Optional social -------------------------------------------------
    reddit_subscribers: int | None = None
    reddit_posts_24h: int | None = None
    sentiment_score: float | None = None

    # --- Optional scores (from previous scoring phases) ------------------
    fundamental_score: float | None = None
    opportunity_score: float | None = None


@dataclass
class FeatureVector:
    """Fixed-length numeric representation of a token for ML models.

    Every field is a ``float``.  Missing source data produces 0.0.
    The order of fields returned by ``to_list()`` is stable and matches
    ``feature_names()`` element-by-element.
    """

    symbol: str = field(repr=True)

    # Market features
    volume_to_mcap: float = 0.0
    mcap_log: float = 0.0
    volume_log: float = 0.0
    ath_distance: float = 0.0
    supply_ratio: float = 0.0  # circulating / implied total (0 if unknown)

    # Dev features (log1p of raw counts)
    commits_30d_log: float = 0.0
    contributors_log: float = 0.0
    stars_log: float = 0.0
    forks_log: float = 0.0

    # Social features
    reddit_subscribers_log: float = 0.0
    reddit_posts_log: float = 0.0
    sentiment_score: float = 0.0

    # Score features
    fundamental_score: float = 0.0
    opportunity_score: float = 0.0

    # --- helpers ---------------------------------------------------------

    def to_list(self) -> list[float]:
        """Return feature values as an ordered list of floats (no symbol)."""
        return [getattr(self, f.name) for f in fields(self) if f.name != "symbol"]

    def feature_names(self) -> list[str]:
        """Return feature names in the same order as ``to_list()``."""
        return [f.name for f in fields(self) if f.name != "symbol"]


class FeatureBuilder:
    """Builds :class:`FeatureVector` instances from :class:`RawTokenData`.

    Stateless — safe to reuse across threads and across calls.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, data: RawTokenData) -> FeatureVector:
        """Convert *data* into a normalised :class:`FeatureVector`.

        Args:
            data: Raw token metrics from any source.

        Returns:
            A :class:`FeatureVector` with every field set to a finite float.
        """
        return FeatureVector(
            symbol=data.symbol,
            # ---- market ------------------------------------------------
            volume_to_mcap=self._safe_ratio(data.volume_24h_usd, data.market_cap_usd),
            mcap_log=self._log1p(data.market_cap_usd),
            volume_log=self._log1p(data.volume_24h_usd),
            ath_distance=self._ath_distance(data.price_usd, data.ath_usd),
            supply_ratio=self._supply_ratio(
                data.circulating_supply, data.market_cap_usd, data.price_usd
            ),
            # ---- dev ---------------------------------------------------
            commits_30d_log=self._log1p(data.commits_30d),
            contributors_log=self._log1p(data.contributors),
            stars_log=self._log1p(data.stars),
            forks_log=self._log1p(data.forks),
            # ---- social ------------------------------------------------
            reddit_subscribers_log=self._log1p(data.reddit_subscribers),
            reddit_posts_log=self._log1p(data.reddit_posts_24h),
            sentiment_score=float(data.sentiment_score or 0.0),
            # ---- scores ------------------------------------------------
            fundamental_score=float(data.fundamental_score or 0.0),
            opportunity_score=float(data.opportunity_score or 0.0),
        )

    def build_batch(self, data_list: list[RawTokenData]) -> list[FeatureVector]:
        """Build a :class:`FeatureVector` for every item in *data_list*.

        Args:
            data_list: Sequence of raw token data; may be empty.

        Returns:
            List of :class:`FeatureVector` in the same order as the input.
        """
        return [self.build(d) for d in data_list]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log1p(value: float | int | None) -> float:
        """Return ``math.log1p(value)`` or 0.0 for None / non-positive."""
        if value is None or value <= 0:
            return 0.0
        return math.log1p(float(value))

    @staticmethod
    def _safe_ratio(numerator: float, denominator: float) -> float:
        """Return numerator / denominator, or 0.0 if denominator is zero."""
        if denominator == 0.0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def _ath_distance(price: float, ath: float) -> float:
        """Return fractional distance below ATH clamped to [0, 1].

        0.0  → price is at or above ATH.
        1.0  → price is at zero (maximum possible distance from ATH).
        """
        if ath <= 0.0 or price >= ath:
            return 0.0
        return min(1.0, (ath - price) / ath)

    @staticmethod
    def _supply_ratio(
        circulating: float | None,
        market_cap: float,
        price: float,
    ) -> float:
        """Return circulating / total-supply estimate from market-cap data.

        If circulating supply is unknown, returns 0.0.
        Implied total supply = market_cap / price (rough estimate).
        """
        if circulating is None or price <= 0.0 or market_cap <= 0.0:
            return 0.0
        implied_total = market_cap / price
        if implied_total <= 0.0:
            return 0.0
        return min(1.0, circulating / implied_total)
