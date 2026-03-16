"""WhitepaperCacheService — whitepaper analysis with DB caching.

Caches :class:`WhitepaperAnalysis` results in the ``ai_analyses`` table
with ``analysis_type='whitepaper'``.  Default TTL is **7 days** (168 h).

Usage mirrors :class:`SummaryCacheService`: the caller queries the DB,
checks freshness, and persists the new analysis when stale.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import structlog

from app.ai.whitepaper_analyzer import WhitepaperAnalysis
from app.models.ai_analysis import AiAnalysis

logger = structlog.get_logger(__name__)

# 7-day default TTL for whitepaper analyses
_DEFAULT_TTL_HOURS: float = 168.0


class WhitepaperCacheService:
    """Manages cached whitepaper analyses for tokens.

    Handles serialization / deserialization and cache freshness checks.
    The actual DB queries and LLM calls are performed by the caller
    so this class remains DB-session-agnostic and fully testable.
    """

    def __init__(self, cache_ttl_hours: float = _DEFAULT_TTL_HOURS) -> None:
        """Initialize with a cache TTL.

        Args:
            cache_ttl_hours: Hours before a cached analysis is stale.
                             Defaults to 168 h (7 days).
        """
        self.cache_ttl_hours = cache_ttl_hours

    # ------------------------------------------------------------------
    # Cache freshness
    # ------------------------------------------------------------------

    def is_cache_fresh(self, analysis: AiAnalysis | None) -> bool:
        """Return ``True`` if *analysis* exists and is within the TTL window."""
        if analysis is None:
            return False
        if analysis.created_at is None:
            return False
        now = datetime.now(tz=UTC)
        age = now - analysis.created_at.replace(tzinfo=UTC)
        return age < timedelta(hours=self.cache_ttl_hours)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_analysis(analysis: WhitepaperAnalysis) -> str:
        """Serialize a :class:`WhitepaperAnalysis` to a JSON string."""
        return json.dumps(
            {
                "summary": analysis.summary,
                "problem_solved": analysis.problem_solved,
                "technology": analysis.technology,
                "token_utility": analysis.token_utility,
                "competitors": analysis.competitors,
                "main_risks": analysis.main_risks,
                "innovation_score": analysis.innovation_score,
                "differentiators": analysis.differentiators,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def parse_cached(analysis: AiAnalysis) -> WhitepaperAnalysis:
        """Deserialize ``AiAnalysis.content`` JSON back to a :class:`WhitepaperAnalysis`."""
        data = json.loads(analysis.content)
        return WhitepaperAnalysis(
            summary=data.get("summary", ""),
            problem_solved=data.get("problem_solved", ""),
            technology=data.get("technology", ""),
            token_utility=data.get("token_utility", ""),
            competitors=data.get("competitors", []),
            main_risks=data.get("main_risks", []),
            innovation_score=float(data.get("innovation_score", 5.0)),
            differentiators=data.get("differentiators", []),
        )

    # ------------------------------------------------------------------
    # Build AiAnalysis for persistence
    # ------------------------------------------------------------------

    def build_analysis(
        self,
        *,
        token_id: int,
        analysis: WhitepaperAnalysis,
        model_used: str,
    ) -> AiAnalysis:
        """Create an :class:`AiAnalysis` ORM object ready for persistence.

        The caller is responsible for adding it to the DB session.

        Args:
            token_id: Foreign key to the ``tokens`` table.
            analysis: The whitepaper analysis to cache.
            model_used: Identifier of the LLM that produced the analysis.

        Returns:
            An unsaved :class:`AiAnalysis` instance.
        """
        return AiAnalysis(
            token_id=token_id,
            analysis_type="whitepaper",
            content=self.serialize_analysis(analysis),
            model_used=model_used,
        )
