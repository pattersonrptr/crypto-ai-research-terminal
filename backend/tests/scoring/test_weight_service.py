"""TDD tests for weight_service — active weight loading with cache + fallback.

Naming: test_<unit>_<scenario>_<expected_outcome>
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.scoring.weight_service import (
    DEFAULT_WEIGHTS,
    apply_weights_to_db,
    get_active_weights,
    invalidate_weight_cache,
)

# ---------------------------------------------------------------------------
# get_active_weights
# ---------------------------------------------------------------------------


class TestGetActiveWeights:
    """Tests for get_active_weights()."""

    @pytest.mark.asyncio()
    async def test_get_active_weights_returns_defaults_when_no_db_row(self) -> None:
        """Must return rebalanced defaults when no active row in DB."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_active_weights(session=mock_session)
        assert result["fundamental"] == pytest.approx(0.25)
        assert result["growth"] == pytest.approx(0.20)
        assert result["narrative"] == pytest.approx(0.15)
        assert result["listing"] == pytest.approx(0.10)
        assert result["risk"] == pytest.approx(0.30)
        assert result["source"] == "default_phase9"

    @pytest.mark.asyncio()
    async def test_get_active_weights_returns_db_row_when_active(self) -> None:
        """Must return calibrated weights from DB when an active row exists."""
        mock_row = MagicMock()
        mock_row.fundamental = 0.35
        mock_row.growth = 0.20
        mock_row.narrative = 0.20
        mock_row.listing = 0.15
        mock_row.risk = 0.10
        mock_row.is_active = True

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await get_active_weights(session=mock_session)
        assert result["fundamental"] == pytest.approx(0.35)
        assert result["growth"] == pytest.approx(0.20)
        assert result["source"] == "calibrated"

    @pytest.mark.asyncio()
    async def test_get_active_weights_uses_redis_cache(self) -> None:
        """Second call must return cached result without hitting DB."""
        mock_redis = AsyncMock()
        # First call: cache miss
        mock_redis.get.return_value = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await get_active_weights(session=mock_session, redis=mock_redis)
        # Cache should have been set
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio()
    async def test_get_active_weights_returns_cached_value(self) -> None:
        """When Redis has cached data, must not query DB."""
        import json

        cached = json.dumps(DEFAULT_WEIGHTS | {"source": "default_phase9"})
        mock_redis = AsyncMock()
        mock_redis.get.return_value = cached.encode()

        mock_session = AsyncMock()

        result = await get_active_weights(session=mock_session, redis=mock_redis)
        assert result["source"] == "default_phase9"
        # DB should NOT have been queried
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# apply_weights_to_db
# ---------------------------------------------------------------------------


class TestApplyWeightsToDb:
    """Tests for apply_weights_to_db()."""

    @pytest.mark.asyncio()
    async def test_apply_weights_persists_new_row(self) -> None:
        """Must insert a new ScoringWeight row with is_active=True."""
        mock_session = AsyncMock()
        # Deactivate query returns empty (no prior active)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await apply_weights_to_db(
            session=mock_session,
            fundamental=0.35,
            growth=0.20,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
        )
        assert result["fundamental"] == pytest.approx(0.35)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_apply_weights_deactivates_previous(self) -> None:
        """Must set is_active=False on previously active row before inserting new."""
        mock_previous = MagicMock()
        mock_previous.is_active = True
        mock_previous.fundamental = 0.30

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_previous
        mock_session.execute.return_value = mock_result

        await apply_weights_to_db(
            session=mock_session,
            fundamental=0.35,
            growth=0.20,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
        )
        assert mock_previous.is_active is False
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_apply_weights_stores_optional_metadata(self) -> None:
        """source_cycle, precision_at_k, k must be stored when provided."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await apply_weights_to_db(
            session=mock_session,
            fundamental=0.35,
            growth=0.20,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
            source_cycle="cycle_2_2019_2021",
            precision_at_k=0.7,
            k=10,
        )
        assert result["source_cycle"] == "cycle_2_2019_2021"
        assert result["precision_at_k"] == pytest.approx(0.7)
        assert result["k"] == 10

    @pytest.mark.asyncio()
    async def test_apply_weights_invalidates_redis_cache(self) -> None:
        """Must delete the Redis cache key after applying new weights."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_redis = AsyncMock()

        await apply_weights_to_db(
            session=mock_session,
            fundamental=0.35,
            growth=0.20,
            narrative=0.20,
            listing=0.15,
            risk=0.10,
            redis=mock_redis,
        )
        mock_redis.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# invalidate_weight_cache
# ---------------------------------------------------------------------------


class TestInvalidateWeightCache:
    """Tests for invalidate_weight_cache()."""

    @pytest.mark.asyncio()
    async def test_invalidate_cache_deletes_key(self) -> None:
        """Must delete the scoring_weights cache key from Redis."""
        mock_redis = AsyncMock()
        await invalidate_weight_cache(redis=mock_redis)
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_invalidate_cache_no_op_without_redis(self) -> None:
        """Must not raise when Redis is None."""
        await invalidate_weight_cache(redis=None)  # Should not raise


# ---------------------------------------------------------------------------
# OpportunityEngine with custom weights
# ---------------------------------------------------------------------------


class TestOpportunityEngineCustomWeights:
    """Tests for OpportunityEngine.full_composite_score() with custom weights."""

    def test_full_composite_with_custom_weights(self) -> None:
        """Custom weights should change the composite score."""
        from app.scoring.opportunity_engine import OpportunityEngine

        default_score = OpportunityEngine.full_composite_score(
            fundamental=1.0,
            growth=0.0,
            narrative=0.0,
            listing=0.0,
            risk=0.0,
        )
        # Default: fundamental weight is 0.25
        assert default_score == pytest.approx(0.25, abs=0.01)

        custom_score = OpportunityEngine.full_composite_score(
            fundamental=1.0,
            growth=0.0,
            narrative=0.0,
            listing=0.0,
            risk=0.0,
            weights={
                "fundamental": 0.50,
                "growth": 0.15,
                "narrative": 0.15,
                "listing": 0.10,
                "risk": 0.10,
            },
        )
        # With custom weight 0.50, should be ~0.50
        assert custom_score == pytest.approx(0.50, abs=0.01)

    def test_full_composite_none_weights_uses_defaults(self) -> None:
        """When weights=None, must use hardcoded defaults."""
        from app.scoring.opportunity_engine import OpportunityEngine

        result = OpportunityEngine.full_composite_score(
            fundamental=0.5,
            growth=0.5,
            narrative=0.5,
            listing=0.5,
            risk=0.5,
            weights=None,
        )
        # All at 0.5: base = 0.5 * (0.30+0.25+0.20+0.15+0.10) = 0.5 * 1.0 = 0.5
        assert result == pytest.approx(0.50, abs=0.01)
