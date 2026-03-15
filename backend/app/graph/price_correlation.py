"""PriceCorrelationBuilder — correlation-based graph edges.

Computes pairwise Pearson correlation from historical price series
and produces :class:`EdgeData` for pairs exceeding a configurable
correlation threshold (default 0.7).

Usage::

    builder = PriceCorrelationBuilder(threshold=0.7)
    edges = builder.build({"BTC": [30000, 31000, ...], "ETH": [2000, 2100, ...]})
    # → [EdgeData(source="BTC", target="ETH", relation_type="correlation", weight=0.97)]
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import structlog

from app.graph.graph_builder import EdgeData

logger = structlog.get_logger(__name__)


class PriceCorrelationBuilder:
    """Build correlation-based graph edges from historical price series.

    Args:
        threshold: Minimum Pearson correlation coefficient for an edge to
                   be created.  Defaults to 0.7.
        use_absolute: If True, use ``|corr|`` so anti-correlated pairs
                      also produce edges.  Defaults to False.
        min_periods: Minimum number of data points required per pair.
                     Pairs with fewer overlapping points are skipped.
    """

    def __init__(
        self,
        threshold: float = 0.7,
        *,
        use_absolute: bool = False,
        min_periods: int = 3,
    ) -> None:
        self.threshold = threshold
        self.use_absolute = use_absolute
        self.min_periods = min_periods

    def build(self, price_series: dict[str, list[float]]) -> list[EdgeData]:
        """Compute pairwise correlations and return edges exceeding threshold.

        Args:
            price_series: Mapping of symbol → list of prices (same time index).
                          Series with fewer than ``min_periods`` points are
                          silently dropped.

        Returns:
            List of :class:`EdgeData` with ``relation_type="correlation"``
            and ``weight`` set to the Pearson coefficient.
        """
        # Filter out short series
        symbols = [sym for sym, prices in price_series.items() if len(prices) >= self.min_periods]
        if len(symbols) < 2:
            return []

        edges: list[EdgeData] = []

        for sym_a, sym_b in combinations(symbols, 2):
            prices_a = price_series[sym_a]
            prices_b = price_series[sym_b]

            # Use the shorter length
            n = min(len(prices_a), len(prices_b))
            if n < self.min_periods:
                continue

            a = np.array(prices_a[:n], dtype=np.float64)
            b = np.array(prices_b[:n], dtype=np.float64)

            # Skip if either series has zero variance
            if np.std(a) == 0.0 or np.std(b) == 0.0:
                continue

            corr = float(np.corrcoef(a, b)[0, 1])

            effective_corr = abs(corr) if self.use_absolute else corr

            if effective_corr >= self.threshold:
                edges.append(
                    EdgeData(
                        source=sym_a,
                        target=sym_b,
                        relation_type="correlation",
                        weight=round(abs(corr), 4),
                    )
                )

        logger.info(
            "price_correlation.built",
            pairs_checked=len(symbols) * (len(symbols) - 1) // 2,
            edges_created=len(edges),
            threshold=self.threshold,
        )
        return edges
