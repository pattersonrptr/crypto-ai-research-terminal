"""NarrativeScorer — score tokens based on narrative alignment.

Evaluates how well a token aligns with currently trending narratives
in the crypto market.
"""

from dataclasses import dataclass

import structlog

from app.ai.llm_provider import LLMProvider
from app.ai.narrative_detector import NarrativeDetectorResult

logger = structlog.get_logger(__name__)


@dataclass
class NarrativeScoreResult:
    """Result of narrative scoring for a token."""

    narrative_fit_score: float  # 0-10 score
    aligned_narratives: list[str]  # Names of aligned narratives
    strongest_narrative: str  # Highest momentum aligned narrative
    narrative_momentum: float  # Average momentum of aligned narratives


class NarrativeScorer:
    """Scores tokens based on narrative alignment.

    Evaluates how well a token fits with currently trending market
    narratives and calculates a composite score.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the scorer.

        Args:
            llm_provider: LLM provider (for potential semantic matching).
        """
        self.llm_provider = llm_provider

    async def score(
        self,
        token_symbol: str,
        token_description: str,
        active_narratives: NarrativeDetectorResult,
    ) -> NarrativeScoreResult:
        """Score a token's narrative alignment.

        Args:
            token_symbol: Token symbol (e.g., "RNDR").
            token_description: Token description.
            active_narratives: Currently detected narratives.

        Returns:
            NarrativeScoreResult with scoring details.
        """
        if not active_narratives.narratives:
            return NarrativeScoreResult(
                narrative_fit_score=0.0,
                aligned_narratives=[],
                strongest_narrative="",
                narrative_momentum=0.0,
            )

        # Find narratives that mention this token
        aligned = []
        for narrative in active_narratives.narratives:
            if token_symbol.upper() in [t.upper() for t in narrative.tokens]:
                aligned.append(narrative)

        if not aligned:
            # Token not in any narrative — low score
            return NarrativeScoreResult(
                narrative_fit_score=1.0,  # Minimum non-zero score
                aligned_narratives=[],
                strongest_narrative="",
                narrative_momentum=0.0,
            )

        # Calculate metrics
        aligned_names = [n.name for n in aligned]

        # Find strongest narrative by momentum
        strongest = max(aligned, key=lambda n: n.momentum_score)
        strongest_name = strongest.name

        # Calculate average momentum
        avg_momentum = sum(n.momentum_score for n in aligned) / len(aligned)

        # Calculate narrative fit score
        # Base: number of aligned narratives (max 3 points)
        # + momentum bonus (max 5 points)
        # + trend bonus (max 2 points)
        base_score = min(3.0, len(aligned) * 1.5)
        momentum_bonus = (avg_momentum / 10.0) * 5.0

        trend_bonus = 0.0
        for narrative in aligned:
            if narrative.trend == "accelerating":
                trend_bonus += 0.7
            elif narrative.trend == "stable":
                trend_bonus += 0.3
        trend_bonus = min(2.0, trend_bonus)

        narrative_fit_score = min(10.0, base_score + momentum_bonus + trend_bonus)

        logger.info(
            "narrative.score.complete",
            token=token_symbol,
            score=narrative_fit_score,
            aligned_count=len(aligned),
        )

        return NarrativeScoreResult(
            narrative_fit_score=round(narrative_fit_score, 1),
            aligned_narratives=aligned_names,
            strongest_narrative=strongest_name,
            narrative_momentum=round(avg_momentum, 1),
        )

    async def score_batch(
        self,
        tokens: list[dict[str, str]],
        active_narratives: NarrativeDetectorResult,
    ) -> list[NarrativeScoreResult]:
        """Score multiple tokens.

        Args:
            tokens: List of dicts with 'symbol' and 'description' keys.
            active_narratives: Currently detected narratives.

        Returns:
            List of NarrativeScoreResults.
        """
        results = []
        for token in tokens:
            result = await self.score(
                token_symbol=token["symbol"],
                token_description=token["description"],
                active_narratives=active_narratives,
            )
            results.append(result)
        return results
