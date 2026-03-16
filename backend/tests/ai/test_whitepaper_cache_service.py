"""TDD tests for WhitepaperCacheService.

Follows the same caching pattern as SummaryCacheService but for whitepaper
analyses with a 7-day TTL.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.ai.whitepaper_analyzer import WhitepaperAnalysis
from app.ai.whitepaper_cache_service import WhitepaperCacheService
from app.models.ai_analysis import AiAnalysis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ANALYSIS = WhitepaperAnalysis(
    summary="Bitcoin is a decentralised digital currency.",
    problem_solved="Double-spending without a trusted third party.",
    technology="Proof-of-work blockchain with SHA-256 mining.",
    token_utility="Medium of exchange and store of value.",
    competitors=["Litecoin", "Bitcoin Cash"],
    main_risks=["Scalability", "Regulation"],
    innovation_score=9.2,
    differentiators=["First mover", "Most secure PoW chain"],
)


def _make_cached(*, hours_ago: float = 0.0) -> AiAnalysis:
    """Return an AiAnalysis mimicking a cached whitepaper row."""
    service = WhitepaperCacheService()
    analysis = AiAnalysis(
        id=1,
        token_id=42,
        analysis_type="whitepaper",
        content=service.serialize_analysis(SAMPLE_ANALYSIS),
        model_used="gemini",
    )
    analysis.created_at = datetime.now(tz=UTC) - timedelta(hours=hours_ago)
    return analysis


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWhitepaperCacheServiceFreshness:
    """Cache freshness logic with 7-day TTL."""

    def test_none_is_not_fresh(self) -> None:
        svc = WhitepaperCacheService()
        assert svc.is_cache_fresh(None) is False

    def test_fresh_within_ttl(self) -> None:
        svc = WhitepaperCacheService()
        cached = _make_cached(hours_ago=24.0)  # 1 day old
        assert svc.is_cache_fresh(cached) is True

    def test_stale_beyond_ttl(self) -> None:
        svc = WhitepaperCacheService()
        cached = _make_cached(hours_ago=170.0)  # >7 days
        assert svc.is_cache_fresh(cached) is False

    def test_custom_ttl(self) -> None:
        svc = WhitepaperCacheService(cache_ttl_hours=1.0)
        cached = _make_cached(hours_ago=2.0)
        assert svc.is_cache_fresh(cached) is False

    def test_missing_created_at_is_stale(self) -> None:
        svc = WhitepaperCacheService()
        analysis = AiAnalysis(
            token_id=42,
            analysis_type="whitepaper",
            content="{}",
            model_used="gemini",
        )
        analysis.created_at = None  # type: ignore[assignment]
        assert svc.is_cache_fresh(analysis) is False


class TestWhitepaperCacheServiceSerialization:
    """Serialize / parse round-trip."""

    def test_serialize_produces_valid_json(self) -> None:
        svc = WhitepaperCacheService()
        raw = svc.serialize_analysis(SAMPLE_ANALYSIS)
        data = json.loads(raw)
        assert data["summary"] == SAMPLE_ANALYSIS.summary
        assert data["innovation_score"] == 9.2

    def test_parse_cached_round_trips(self) -> None:
        svc = WhitepaperCacheService()
        cached = _make_cached()
        result = svc.parse_cached(cached)
        assert result.summary == SAMPLE_ANALYSIS.summary
        assert result.competitors == SAMPLE_ANALYSIS.competitors
        assert result.innovation_score == SAMPLE_ANALYSIS.innovation_score

    def test_build_analysis_returns_ai_analysis(self) -> None:
        svc = WhitepaperCacheService()
        obj = svc.build_analysis(
            token_id=42,
            analysis=SAMPLE_ANALYSIS,
            model_used="gemini",
        )
        assert isinstance(obj, AiAnalysis)
        assert obj.analysis_type == "whitepaper"
        assert obj.token_id == 42
        assert obj.model_used == "gemini"
        # content must be parseable back
        parsed = svc.parse_cached(obj)
        assert parsed.technology == SAMPLE_ANALYSIS.technology
