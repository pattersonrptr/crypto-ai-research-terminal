"""SummaryCacheService — AI summary generation with DB caching.

Wraps :class:`SummaryGenerator` with a caching layer backed by the
``ai_analyses`` table.  When a summary is requested:

1. Check DB for a cached ``AiAnalysis`` with ``analysis_type='summary'``
   for the given ``token_id``.
2. If the cached entry is fresher than ``cache_ttl_hours``, return it.
3. Otherwise, call ``SummaryGenerator.generate()`` and persist the result.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import structlog

from app.ai.summary_generator import ProjectSummary
from app.models.ai_analysis import AiAnalysis

logger = structlog.get_logger(__name__)


class SummaryCacheService:
    """Manages cached AI-generated summaries for tokens.

    This service handles serialization / deserialization and cache freshness
    checks.  The actual DB queries and LLM calls are done by the caller
    (route handler or job) to keep this class DB-session-agnostic and testable.
    """

    def __init__(self, cache_ttl_hours: float = 24.0) -> None:
        """Initialize with a cache TTL.

        Args:
            cache_ttl_hours: Number of hours before a cached analysis is
                             considered stale.  Defaults to 24h.
        """
        self.cache_ttl_hours = cache_ttl_hours

    # ------------------------------------------------------------------
    # Cache freshness
    # ------------------------------------------------------------------

    def is_cache_fresh(self, analysis: AiAnalysis | None) -> bool:
        """Return True if *analysis* exists and is within the TTL window."""
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
    def serialize_summary(summary: ProjectSummary) -> str:
        """Serialize a :class:`ProjectSummary` to a JSON string."""
        return json.dumps(
            {
                "summary_text": summary.summary_text,
                "key_strengths": summary.key_strengths,
                "key_risks": summary.key_risks,
                "investment_thesis": summary.investment_thesis,
                "target_audience": summary.target_audience,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def parse_cached(analysis: AiAnalysis) -> ProjectSummary:
        """Deserialize an ``AiAnalysis.content`` JSON back to a :class:`ProjectSummary`."""
        data = json.loads(analysis.content)
        return ProjectSummary(
            summary_text=data.get("summary_text", ""),
            key_strengths=data.get("key_strengths", []),
            key_risks=data.get("key_risks", []),
            investment_thesis=data.get("investment_thesis", ""),
            target_audience=data.get("target_audience", ""),
        )

    # ------------------------------------------------------------------
    # Build AiAnalysis for persistence
    # ------------------------------------------------------------------

    def build_analysis(
        self,
        *,
        token_id: int,
        summary: ProjectSummary,
        model_used: str,
    ) -> AiAnalysis:
        """Create an :class:`AiAnalysis` ORM object ready for persistence.

        The caller is responsible for adding it to the DB session.

        Args:
            token_id: Foreign key to the ``tokens`` table.
            summary: The generated summary to cache.
            model_used: Identifier of the LLM that produced the summary.

        Returns:
            An unsaved :class:`AiAnalysis` instance.
        """
        return AiAnalysis(
            token_id=token_id,
            analysis_type="summary",
            content=self.serialize_summary(summary),
            model_used=model_used,
        )
