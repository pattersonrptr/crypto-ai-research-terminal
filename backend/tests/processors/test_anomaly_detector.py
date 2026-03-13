"""TDD tests for AnomalyDetector — statistical anomaly detection."""

from app.processors.anomaly_detector import AnomalyDetector


class TestAnomalyDetectorZScore:
    """Tests for AnomalyDetector.z_score() method."""

    def test_z_score_above_mean(self) -> None:
        """z_score() returns positive value when value is above mean."""
        result = AnomalyDetector.z_score(value=150.0, mean=100.0, std=25.0)
        assert result == 2.0  # (150-100)/25

    def test_z_score_below_mean(self) -> None:
        """z_score() returns negative value when value is below mean."""
        result = AnomalyDetector.z_score(value=50.0, mean=100.0, std=25.0)
        assert result == -2.0  # (50-100)/25

    def test_z_score_at_mean(self) -> None:
        """z_score() returns 0.0 when value equals mean."""
        result = AnomalyDetector.z_score(value=100.0, mean=100.0, std=25.0)
        assert result == 0.0

    def test_z_score_zero_std(self) -> None:
        """z_score() returns 0.0 when std is zero (no variance)."""
        result = AnomalyDetector.z_score(value=150.0, mean=100.0, std=0.0)
        assert result == 0.0


class TestAnomalyDetectorAnomalyScore:
    """Tests for AnomalyDetector.anomaly_score() method."""

    def test_anomaly_score_normal_value(self) -> None:
        """anomaly_score() returns low score for values within 1 std."""
        # Value at mean (z=0) should give score near 0
        result = AnomalyDetector.anomaly_score(value=100.0, mean=100.0, std=25.0)
        assert result < 0.3

    def test_anomaly_score_outlier_value(self) -> None:
        """anomaly_score() returns high score for values far from mean."""
        # Value 4 std above mean should be clearly anomalous
        result = AnomalyDetector.anomaly_score(value=200.0, mean=100.0, std=25.0)
        assert result > 0.7

    def test_anomaly_score_range(self) -> None:
        """anomaly_score() returns values between 0.0 and 1.0."""
        result = AnomalyDetector.anomaly_score(value=200.0, mean=100.0, std=25.0)
        assert 0.0 <= result <= 1.0

    def test_anomaly_score_zero_std(self) -> None:
        """anomaly_score() returns 0.0 when std is zero."""
        result = AnomalyDetector.anomaly_score(value=150.0, mean=100.0, std=0.0)
        assert result == 0.0


class TestAnomalyDetectorDetectFromHistory:
    """Tests for AnomalyDetector.detect_from_history() method."""

    def test_detect_from_history_normal(self) -> None:
        """detect_from_history() returns low anomaly for values within historical range."""
        history = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 97.0]
        current = 101.0
        result = AnomalyDetector.detect_from_history(current, history)
        assert result["anomaly_score"] < 0.3

    def test_detect_from_history_outlier(self) -> None:
        """detect_from_history() returns high anomaly for values far from historical range."""
        history = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 97.0]
        current = 200.0  # Way above historical values
        result = AnomalyDetector.detect_from_history(current, history)
        assert result["anomaly_score"] > 0.7

    def test_detect_from_history_returns_stats(self) -> None:
        """detect_from_history() returns z_score, mean, std, and anomaly_score."""
        history = [100.0, 100.0, 100.0, 100.0]
        current = 100.0
        result = AnomalyDetector.detect_from_history(current, history)
        assert "z_score" in result
        assert "mean" in result
        assert "std" in result
        assert "anomaly_score" in result

    def test_detect_from_history_empty_history(self) -> None:
        """detect_from_history() handles empty history gracefully."""
        result = AnomalyDetector.detect_from_history(100.0, [])
        assert result["anomaly_score"] == 0.0
        assert result["z_score"] == 0.0

    def test_detect_from_history_single_value(self) -> None:
        """detect_from_history() handles single-value history (zero variance)."""
        result = AnomalyDetector.detect_from_history(150.0, [100.0])
        assert result["anomaly_score"] == 0.0


class TestAnomalyDetectorDetectVolumeAnomaly:
    """Tests for AnomalyDetector.detect_volume_anomaly() method."""

    def test_detect_volume_anomaly_spike(self) -> None:
        """detect_volume_anomaly() detects unusual volume spikes."""
        volume_history = [1e6, 1.1e6, 0.9e6, 1e6, 1.05e6, 0.95e6, 1e6]
        current_volume = 5e6  # 5x historical average
        result = AnomalyDetector.detect_volume_anomaly(current_volume, volume_history)
        assert result["is_anomaly"] is True
        assert result["anomaly_score"] > 0.7

    def test_detect_volume_anomaly_normal(self) -> None:
        """detect_volume_anomaly() returns low anomaly for normal volume."""
        volume_history = [1e6, 1.1e6, 0.9e6, 1e6, 1.05e6, 0.95e6, 1e6]
        current_volume = 1.02e6
        result = AnomalyDetector.detect_volume_anomaly(current_volume, volume_history)
        assert result["is_anomaly"] is False
        assert result["anomaly_score"] < 0.5


class TestAnomalyDetectorDetectPriceAnomaly:
    """Tests for AnomalyDetector.detect_price_anomaly() method."""

    def test_detect_price_anomaly_pump(self) -> None:
        """detect_price_anomaly() detects unusual price pumps."""
        price_history = [1.0, 1.01, 0.99, 1.0, 1.02, 0.98, 1.0]
        current_price = 2.0  # 100% increase
        result = AnomalyDetector.detect_price_anomaly(current_price, price_history)
        assert result["is_anomaly"] is True

    def test_detect_price_anomaly_normal(self) -> None:
        """detect_price_anomaly() returns low anomaly for normal price movement."""
        price_history = [1.0, 1.01, 0.99, 1.0, 1.02, 0.98, 1.0]
        current_price = 1.01
        result = AnomalyDetector.detect_price_anomaly(current_price, price_history)
        assert result["is_anomaly"] is False
