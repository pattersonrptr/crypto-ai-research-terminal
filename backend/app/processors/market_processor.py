"""MarketProcessor — derives market-intelligence features from raw market data."""

from typing import Any


class MarketProcessor:
    """Computes derived market features: volume/mcap ratio, velocity, ATH distance."""

    @staticmethod
    def volume_mcap_ratio(volume_24h_usd: float, market_cap_usd: float) -> float:
        """Return the 24-hour volume-to-market-cap ratio.

        A high ratio may indicate elevated trading activity or potential manipulation.
        Returns 0.0 when market cap is zero to avoid division by zero.
        """
        if market_cap_usd == 0.0:
            return 0.0
        return volume_24h_usd / market_cap_usd

    @staticmethod
    def price_velocity(current_price: float, previous_price: float) -> float:
        """Return the percentage price change between two observations.

        Returns 0.0 when ``previous_price`` is zero.
        """
        if previous_price == 0.0:
            return 0.0
        return (current_price - previous_price) / previous_price * 100.0

    @staticmethod
    def ath_distance(current_price: float, ath_price: float) -> float:
        """Return how far below ATH the current price is, as a percentage.

        Returns 0.0 when ``ath_price`` is zero.
        """
        if ath_price == 0.0:
            return 0.0
        return (ath_price - current_price) / ath_price * 100.0

    @classmethod
    def process(cls, raw: dict[str, Any], previous_price: float | None = None) -> dict[str, Any]:
        """Apply all market-feature computations to a raw market-data dict.

        Returns a new dict containing all original fields plus the derived
        ``volume_mcap_ratio``, ``price_velocity``, and ``ath_distance_pct`` keys.
        """
        result = dict(raw)
        result["volume_mcap_ratio"] = cls.volume_mcap_ratio(
            volume_24h_usd=raw.get("volume_24h_usd", 0.0),
            market_cap_usd=raw.get("market_cap_usd", 0.0),
        )
        result["price_velocity"] = cls.price_velocity(
            current_price=raw.get("price_usd", 0.0),
            previous_price=previous_price if previous_price is not None else 0.0,
        )
        result["ath_distance_pct"] = cls.ath_distance(
            current_price=raw.get("price_usd", 0.0),
            ath_price=raw.get("ath_usd", 0.0),
        )
        return result
