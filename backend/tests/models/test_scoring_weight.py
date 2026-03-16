"""Tests for models.scoring_weight — persisted calibrated weights.

TDD: RED phase — tests written first.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.models.scoring_weight import ScoringWeight


class TestScoringWeightModel:
    """Tests for the ScoringWeight ORM model."""

    def test_tablename(self) -> None:
        assert ScoringWeight.__tablename__ == "scoring_weights"

    def test_fields_exist(self) -> None:
        sw = ScoringWeight(
            fundamental=0.35,
            growth=0.25,
            narrative=0.15,
            listing=0.15,
            risk=0.10,
            source_cycle="cycle_2_2019_2021",
            precision_at_k=0.70,
            k=10,
            is_active=True,
        )
        assert sw.fundamental == pytest.approx(0.35)
        assert sw.growth == pytest.approx(0.25)
        assert sw.narrative == pytest.approx(0.15)
        assert sw.listing == pytest.approx(0.15)
        assert sw.risk == pytest.approx(0.10)
        assert sw.source_cycle == "cycle_2_2019_2021"
        assert sw.precision_at_k == pytest.approx(0.70)
        assert sw.k == 10
        assert sw.is_active is True

    def test_total_property(self) -> None:
        sw = ScoringWeight(
            fundamental=0.30,
            growth=0.25,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
        )
        assert sw.total == pytest.approx(1.0)

    def test_to_weight_set(self) -> None:
        """to_weight_set() must return a WeightSet with matching values."""
        from app.backtesting.weight_calibrator import WeightSet

        sw = ScoringWeight(
            fundamental=0.35,
            growth=0.25,
            narrative=0.15,
            listing=0.15,
            risk=0.10,
        )
        ws = sw.to_weight_set()
        assert isinstance(ws, WeightSet)
        assert ws.fundamental == pytest.approx(0.35)
        assert ws.growth == pytest.approx(0.25)
        assert ws.risk == pytest.approx(0.10)

    def test_repr_contains_key_info(self) -> None:
        sw = ScoringWeight(
            id=1,
            fundamental=0.30,
            growth=0.25,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
            is_active=True,
        )
        r = repr(sw)
        assert "ScoringWeight" in r
        assert "active=True" in r
