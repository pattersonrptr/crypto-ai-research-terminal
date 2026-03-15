"""Tests for PriceCorrelationBuilder — correlation-based graph edges.

Computes pairwise Pearson correlation from historical price series
and produces edges where |correlation| > threshold.
"""

from __future__ import annotations

import pytest

from app.graph.price_correlation import PriceCorrelationBuilder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _price_series() -> dict[str, list[float]]:
    """Return synthetic price series for 3 tokens."""
    return {
        "BTC": [30000.0, 31000.0, 32000.0, 31500.0, 33000.0, 34000.0, 35000.0],
        "ETH": [2000.0, 2100.0, 2200.0, 2150.0, 2300.0, 2400.0, 2500.0],
        "DOGE": [0.08, 0.07, 0.09, 0.06, 0.08, 0.07, 0.085],
    }


def _perfectly_correlated() -> dict[str, list[float]]:
    """Two tokens with perfectly correlated prices."""
    return {
        "A": [1.0, 2.0, 3.0, 4.0, 5.0],
        "B": [10.0, 20.0, 30.0, 40.0, 50.0],
    }


def _perfectly_anti_correlated() -> dict[str, list[float]]:
    """Two tokens with perfectly anti-correlated prices."""
    return {
        "A": [1.0, 2.0, 3.0, 4.0, 5.0],
        "B": [50.0, 40.0, 30.0, 20.0, 10.0],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPriceCorrelationBuilder:
    """PriceCorrelationBuilder computes pairwise correlations."""

    def test_build_returns_edges_for_high_correlation(self) -> None:
        """BTC and ETH move together → should produce a correlation edge."""
        builder = PriceCorrelationBuilder(threshold=0.7)
        edges = builder.build(_price_series())
        # BTC-ETH should be correlated; DOGE is random
        symbols_in_edges = {(e.source, e.target) for e in edges}
        assert any(
            ("BTC" in pair and "ETH" in pair) for pair in [frozenset(p) for p in symbols_in_edges]
        )

    def test_perfect_correlation_produces_edge(self) -> None:
        builder = PriceCorrelationBuilder(threshold=0.7)
        edges = builder.build(_perfectly_correlated())
        assert len(edges) == 1
        assert edges[0].relation_type == "correlation"
        assert edges[0].weight == pytest.approx(1.0, abs=0.01)

    def test_anti_correlation_excluded_by_default(self) -> None:
        """Anti-correlated pairs are excluded when use_absolute=False."""
        builder = PriceCorrelationBuilder(threshold=0.7, use_absolute=False)
        edges = builder.build(_perfectly_anti_correlated())
        assert len(edges) == 0

    def test_anti_correlation_included_when_absolute(self) -> None:
        """Anti-correlated pairs are included when use_absolute=True."""
        builder = PriceCorrelationBuilder(threshold=0.7, use_absolute=True)
        edges = builder.build(_perfectly_anti_correlated())
        assert len(edges) == 1

    def test_empty_price_series_returns_no_edges(self) -> None:
        builder = PriceCorrelationBuilder()
        edges = builder.build({})
        assert edges == []

    def test_single_token_returns_no_edges(self) -> None:
        builder = PriceCorrelationBuilder()
        edges = builder.build({"BTC": [100.0, 200.0, 300.0]})
        assert edges == []

    def test_short_series_skipped(self) -> None:
        """Need at least 3 data points for meaningful correlation."""
        builder = PriceCorrelationBuilder(min_periods=3)
        edges = builder.build({"A": [1.0, 2.0], "B": [10.0, 20.0]})
        assert edges == []

    def test_edge_weight_is_correlation_coefficient(self) -> None:
        builder = PriceCorrelationBuilder(threshold=0.0)
        edges = builder.build(_perfectly_correlated())
        assert len(edges) == 1
        assert 0.0 <= edges[0].weight <= 1.0

    def test_custom_threshold(self) -> None:
        """With threshold=0.99, only near-perfect correlation passes."""
        builder = PriceCorrelationBuilder(threshold=0.99)
        edges = builder.build(_price_series())
        # BTC-ETH are correlated ~0.97, might not pass 0.99
        # This just tests the threshold is respected
        for edge in edges:
            assert edge.weight >= 0.99
