"""Tests for Normalizer utility functions.

Validates min-max normalisation helpers used across all scoring modules.
"""

import pytest

from app.processors.normalizer import clamp, min_max_normalize, normalize_series


class TestMinMaxNormalize:
    """min_max_normalize maps a value to [0, 1] given min and max bounds."""

    def test_min_max_normalize_midpoint_returns_half(self) -> None:
        result = min_max_normalize(value=5.0, min_val=0.0, max_val=10.0)
        assert result == pytest.approx(0.5)

    def test_min_max_normalize_at_min_returns_zero(self) -> None:
        result = min_max_normalize(value=0.0, min_val=0.0, max_val=10.0)
        assert result == pytest.approx(0.0)

    def test_min_max_normalize_at_max_returns_one(self) -> None:
        result = min_max_normalize(value=10.0, min_val=0.0, max_val=10.0)
        assert result == pytest.approx(1.0)

    def test_min_max_normalize_equal_min_max_returns_zero(self) -> None:
        result = min_max_normalize(value=5.0, min_val=5.0, max_val=5.0)
        assert result == 0.0

    def test_min_max_normalize_value_below_min_is_clamped_to_zero(self) -> None:
        result = min_max_normalize(value=-1.0, min_val=0.0, max_val=10.0)
        assert result == pytest.approx(0.0)

    def test_min_max_normalize_value_above_max_is_clamped_to_one(self) -> None:
        result = min_max_normalize(value=15.0, min_val=0.0, max_val=10.0)
        assert result == pytest.approx(1.0)


class TestNormalizeSeries:
    """normalize_series applies min-max normalisation to an entire list."""

    def test_normalize_series_returns_list_of_same_length(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = normalize_series(values)
        assert len(result) == len(values)

    def test_normalize_series_min_maps_to_zero(self) -> None:
        result = normalize_series([0.0, 5.0, 10.0])
        assert result[0] == pytest.approx(0.0)

    def test_normalize_series_max_maps_to_one(self) -> None:
        result = normalize_series([0.0, 5.0, 10.0])
        assert result[-1] == pytest.approx(1.0)

    def test_normalize_series_all_equal_values_returns_zeros(self) -> None:
        result = normalize_series([7.0, 7.0, 7.0])
        assert all(v == 0.0 for v in result)

    def test_normalize_series_empty_list_returns_empty_list(self) -> None:
        result = normalize_series([])
        assert result == []


class TestClamp:
    """clamp restricts a value to [low, high]."""

    def test_clamp_value_within_range_unchanged(self) -> None:
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_clamp_value_below_low_returns_low(self) -> None:
        assert clamp(-1.0, 0.0, 10.0) == 0.0

    def test_clamp_value_above_high_returns_high(self) -> None:
        assert clamp(20.0, 0.0, 10.0) == 10.0
