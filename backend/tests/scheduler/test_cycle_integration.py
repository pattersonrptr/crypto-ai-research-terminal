"""TDD tests for CycleDetector integration in daily_collection_job.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analysis.cycle_detector import CyclePhase, CycleResult
from app.scoring.opportunity_engine import OpportunityEngine

# ---------------------------------------------------------------------------
# OpportunityEngine.cycle_adjusted_score integration
# ---------------------------------------------------------------------------


class TestCycleAdjustedScoreIntegration:
    """Verify cycle_adjusted_score changes the final opportunity score."""

    def test_bull_phase_boosts_opportunity_score(self) -> None:
        """Bull phase should increase opportunity score by ~10%."""
        base = 0.60
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.BULL)
        assert adjusted > base
        assert adjusted == pytest.approx(base * 1.10, abs=0.01)

    def test_bear_phase_dampens_opportunity_score(self) -> None:
        """Bear phase should decrease opportunity score by ~25%."""
        base = 0.60
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.BEAR)
        assert adjusted < base
        assert adjusted == pytest.approx(base * 0.75, abs=0.01)

    def test_accumulation_phase_neutral(self) -> None:
        """Accumulation phase should not change the score."""
        base = 0.60
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.ACCUMULATION)
        assert adjusted == pytest.approx(base, abs=0.01)

    def test_distribution_phase_dampens_slightly(self) -> None:
        """Distribution phase should decrease score by ~10%."""
        base = 0.60
        adjusted = OpportunityEngine.cycle_adjusted_score(base, CyclePhase.DISTRIBUTION)
        assert adjusted == pytest.approx(base * 0.90, abs=0.01)

    def test_none_phase_returns_base_unchanged(self) -> None:
        """When cycle phase is None, score should be unchanged."""
        base = 0.60
        adjusted = OpportunityEngine.cycle_adjusted_score(base, None)
        assert adjusted == pytest.approx(base, abs=0.001)


# ---------------------------------------------------------------------------
# detect_cycle_phase helper
# ---------------------------------------------------------------------------


class TestDetectCyclePhase:
    """Tests for detect_cycle_phase() used in daily_collection_job."""

    @pytest.mark.asyncio()
    async def test_detect_cycle_phase_returns_phase(self) -> None:
        """detect_cycle_phase must return a CyclePhase enum."""
        from app.scheduler.jobs import detect_cycle_phase

        mock_indicators = MagicMock()
        mock_result = CycleResult(
            phase=CyclePhase.BULL,
            confidence=0.8,
            indicators=mock_indicators,
        )

        with (
            patch(
                "app.scheduler.jobs.CycleDataCollector",
            ) as mock_cdc_cls,
        ):
            mock_cdc = AsyncMock()
            mock_cdc.collect_indicators.return_value = mock_indicators
            mock_cdc_cls.return_value = mock_cdc

            with patch(
                "app.scheduler.jobs.CycleDetector.classify",
                return_value=mock_result,
            ):
                phase = await detect_cycle_phase()

        assert phase == CyclePhase.BULL

    @pytest.mark.asyncio()
    async def test_detect_cycle_phase_returns_none_on_error(self) -> None:
        """detect_cycle_phase must return None when detection fails."""
        from app.scheduler.jobs import detect_cycle_phase

        with patch(
            "app.scheduler.jobs.CycleDataCollector",
        ) as mock_cdc_cls:
            mock_cdc = AsyncMock()
            mock_cdc.collect_indicators.side_effect = RuntimeError("API down")
            mock_cdc_cls.return_value = mock_cdc

            phase = await detect_cycle_phase()

        assert phase is None

    @pytest.mark.asyncio()
    async def test_detect_cycle_phase_logs_result(self) -> None:
        """detect_cycle_phase must log the detected phase."""
        from app.scheduler.jobs import detect_cycle_phase

        mock_indicators = MagicMock()
        mock_result = CycleResult(
            phase=CyclePhase.ACCUMULATION,
            confidence=0.6,
            indicators=mock_indicators,
        )

        with (
            patch(
                "app.scheduler.jobs.CycleDataCollector",
            ) as mock_cdc_cls,
            patch(
                "app.scheduler.jobs.CycleDetector.classify",
                return_value=mock_result,
            ),
            patch("app.scheduler.jobs.logger") as mock_logger,
        ):
            mock_cdc = AsyncMock()
            mock_cdc.collect_indicators.return_value = mock_indicators
            mock_cdc_cls.return_value = mock_cdc

            await detect_cycle_phase()

        # Should have logged something about cycle detection
        mock_logger.bind.return_value.info.assert_called()
