"""AnomalyDetector — statistical anomaly detection for market metrics."""

import statistics
from typing import Any


class AnomalyDetector:
    """Detects statistical anomalies in volume, price, and other metrics."""

    # Default threshold for anomaly classification (z-score)
    ANOMALY_THRESHOLD = 2.0

    @staticmethod
    def z_score(value: float, mean: float, std: float) -> float:
        """Calculate the z-score (standard deviations from mean).

        Args:
            value: The value to evaluate.
            mean: Historical mean.
            std: Historical standard deviation.

        Returns:
            Z-score. Returns 0.0 if std is zero.
        """
        if std == 0.0:
            return 0.0
        return (value - mean) / std

    @classmethod
    def anomaly_score(cls, value: float, mean: float, std: float) -> float:
        """Calculate an anomaly score between 0.0 and 1.0.

        Uses the cumulative distribution function to map z-score to a
        probability-like score. Higher scores indicate more anomalous values.

        Args:
            value: The value to evaluate.
            mean: Historical mean.
            std: Historical standard deviation.

        Returns:
            Anomaly score between 0.0 and 1.0.
        """
        if std == 0.0:
            return 0.0

        z = abs(cls.z_score(value, mean, std))
        # Map z-score to 0-1 range using a sigmoid-like function
        # z=0 -> ~0, z=2 -> ~0.76, z=3 -> ~0.90, z=4+ -> ~0.98
        return 1.0 - (1.0 / (1.0 + z * z / 4.0))

    @classmethod
    def detect_from_history(cls, current: float, history: list[float]) -> dict[str, Any]:
        """Detect anomalies by comparing current value to historical distribution.

        Args:
            current: The current value to evaluate.
            history: List of historical values.

        Returns:
            Dict with z_score, mean, std, and anomaly_score.
        """
        if len(history) < 2:
            return {
                "z_score": 0.0,
                "mean": history[0] if history else current,
                "std": 0.0,
                "anomaly_score": 0.0,
            }

        mean = statistics.mean(history)
        std = statistics.stdev(history)

        z = cls.z_score(current, mean, std)
        score = cls.anomaly_score(current, mean, std)

        return {
            "z_score": z,
            "mean": mean,
            "std": std,
            "anomaly_score": score,
        }

    @classmethod
    def detect_volume_anomaly(
        cls, current_volume: float, volume_history: list[float]
    ) -> dict[str, Any]:
        """Detect unusual trading volume spikes.

        Args:
            current_volume: Current trading volume.
            volume_history: List of historical volume values.

        Returns:
            Dict with z_score, anomaly_score, and is_anomaly boolean.
        """
        result = cls.detect_from_history(current_volume, volume_history)
        result["is_anomaly"] = abs(result["z_score"]) >= cls.ANOMALY_THRESHOLD
        return result

    @classmethod
    def detect_price_anomaly(
        cls, current_price: float, price_history: list[float]
    ) -> dict[str, Any]:
        """Detect unusual price movements.

        Args:
            current_price: Current price.
            price_history: List of historical price values.

        Returns:
            Dict with z_score, anomaly_score, and is_anomaly boolean.
        """
        result = cls.detect_from_history(current_price, price_history)
        result["is_anomaly"] = abs(result["z_score"]) >= cls.ANOMALY_THRESHOLD
        return result
