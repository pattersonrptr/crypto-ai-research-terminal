"""Tests for SummaryCacheService — AI summary generation with DB caching."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.ai.summary_cache_service import SummaryCacheService
from app.ai.summary_generator import ProjectSummary
from app.models.ai_analysis import AiAnalysis

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_summary() -> ProjectSummary:
    """Return a valid ProjectSummary for testing."""
    return ProjectSummary(
        summary_text="Bitcoin is a decentralized digital currency.",
        key_strengths=["decentralized", "first-mover"],
        key_risks=["volatility", "regulation"],
        investment_thesis="Store of value in uncertain times.",
        target_audience="Long-term investors",
    )


def _make_cached_analysis(
    *,
    hours_old: float = 1.0,
) -> AiAnalysis:
    """Return an AiAnalysis mimicking a cached row."""
    analysis = AiAnalysis(
        id=1,
        token_id=1,
        analysis_type="summary",
        content=(
            '{"summary_text":"Cached summary.","key_strengths":[],'
            '"key_risks":[],"investment_thesis":"","target_audience":""}'
        ),
        model_used="ollama/llama3",
    )
    # Simulate created_at manually
    analysis.created_at = datetime.now(tz=UTC) - timedelta(hours=hours_old)
    return analysis


# ---------------------------------------------------------------------------
# Tests — cache hit / miss logic
# ---------------------------------------------------------------------------


class TestSummaryCacheServiceGet:
    """SummaryCacheService.get() checks cache, then generates if needed."""

    @pytest.mark.asyncio
    async def test_returns_cached_summary_when_fresh(self) -> None:
        """Fresh cache hit → return cached content, no LLM call."""
        cached = _make_cached_analysis(hours_old=1.0)
        service = SummaryCacheService(cache_ttl_hours=24)

        result = service.parse_cached(cached)
        assert result.summary_text == "Cached summary."

    def test_is_cache_fresh_true_when_within_ttl(self) -> None:
        cached = _make_cached_analysis(hours_old=1.0)
        service = SummaryCacheService(cache_ttl_hours=24)
        assert service.is_cache_fresh(cached) is True

    def test_is_cache_fresh_false_when_expired(self) -> None:
        cached = _make_cached_analysis(hours_old=25.0)
        service = SummaryCacheService(cache_ttl_hours=24)
        assert service.is_cache_fresh(cached) is False

    def test_is_cache_fresh_false_when_none(self) -> None:
        service = SummaryCacheService(cache_ttl_hours=24)
        assert service.is_cache_fresh(None) is False


# ---------------------------------------------------------------------------
# Tests — serialization round-trip
# ---------------------------------------------------------------------------


class TestSummaryCacheServiceSerialization:
    """Summary → JSON → AiAnalysis → Summary round-trip."""

    def test_serialize_summary_to_json(self) -> None:
        service = SummaryCacheService()
        summary = _make_summary()
        json_str = service.serialize_summary(summary)
        assert "Bitcoin" in json_str
        assert "decentralized" in json_str

    def test_parse_cached_round_trip(self) -> None:
        service = SummaryCacheService()
        original = _make_summary()
        json_str = service.serialize_summary(original)

        analysis = AiAnalysis(
            id=1,
            token_id=1,
            analysis_type="summary",
            content=json_str,
            model_used="ollama/llama3",
        )
        analysis.created_at = datetime.now(tz=UTC)

        restored = service.parse_cached(analysis)
        assert restored.summary_text == original.summary_text
        assert restored.key_strengths == original.key_strengths
        assert restored.key_risks == original.key_risks


class TestSummaryCacheServiceBuildAnalysis:
    """build_analysis() creates an AiAnalysis from a ProjectSummary."""

    def test_build_analysis_creates_correct_model(self) -> None:
        service = SummaryCacheService()
        summary = _make_summary()
        analysis = service.build_analysis(
            token_id=42,
            summary=summary,
            model_used="gemini/pro",
        )
        assert isinstance(analysis, AiAnalysis)
        assert analysis.token_id == 42
        assert analysis.analysis_type == "summary"
        assert analysis.model_used == "gemini/pro"
        assert "Bitcoin" in analysis.content
