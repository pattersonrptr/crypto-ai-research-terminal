"""Tests for NarrativeScorer — TDD [RED] phase."""

import pytest

from app.ai.llm_provider import LLMProvider
from app.ai.narrative_detector import Narrative, NarrativeDetectorResult
from app.scoring.narrative_scorer import NarrativeScorer, NarrativeScoreResult


class TestNarrativeScoreResult:
    """Tests for NarrativeScoreResult dataclass."""

    def test_narrative_score_result_has_required_fields(self) -> None:
        """NarrativeScoreResult should have all required fields."""
        result = NarrativeScoreResult(
            narrative_fit_score=7.5,
            aligned_narratives=["AI + Blockchain", "Infrastructure"],
            strongest_narrative="AI + Blockchain",
            narrative_momentum=8.0,
        )
        assert result.narrative_fit_score == 7.5
        assert "AI + Blockchain" in result.aligned_narratives
        assert result.strongest_narrative == "AI + Blockchain"
        assert result.narrative_momentum == 8.0


class TestNarrativeScorerInit:
    """Tests for NarrativeScorer initialization."""

    def test_init_requires_llm_provider(self) -> None:
        """Should accept an LLMProvider instance."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)
        assert scorer.llm_provider is provider


class TestNarrativeScorerScore:
    """Tests for NarrativeScorer score method."""

    @pytest.fixture
    def sample_narratives(self) -> NarrativeDetectorResult:
        """Sample narratives for testing."""
        return NarrativeDetectorResult(
            narratives=[
                Narrative(
                    name="AI + Blockchain",
                    momentum_score=8.5,
                    trend="accelerating",
                    tokens=["FET", "RNDR", "TAO"],
                    keywords=["AI agents", "GPU compute"],
                ),
                Narrative(
                    name="Layer 2 Scaling",
                    momentum_score=7.0,
                    trend="stable",
                    tokens=["ARB", "OP", "MATIC"],
                    keywords=["scaling", "rollups"],
                ),
                Narrative(
                    name="DePIN",
                    momentum_score=6.5,
                    trend="accelerating",
                    tokens=["HNT", "MOBILE", "RNDR"],
                    keywords=["infrastructure", "IoT"],
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_score_returns_narrative_score_result(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should return NarrativeScoreResult."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="RNDR",
            token_description="GPU rendering network",
            active_narratives=sample_narratives,
        )

        assert isinstance(result, NarrativeScoreResult)

    @pytest.mark.asyncio
    async def test_score_identifies_aligned_narratives(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should identify narratives the token aligns with."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="RNDR",
            token_description="GPU rendering network",
            active_narratives=sample_narratives,
        )

        # RNDR is in AI + Blockchain and DePIN narratives
        assert len(result.aligned_narratives) >= 1

    @pytest.mark.asyncio
    async def test_score_returns_strongest_narrative(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should return the strongest aligned narrative."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="RNDR",
            token_description="GPU rendering network",
            active_narratives=sample_narratives,
        )

        # Strongest should be from aligned narratives
        if result.aligned_narratives:
            assert result.strongest_narrative in result.aligned_narratives

    @pytest.mark.asyncio
    async def test_score_calculates_narrative_fit_score(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should calculate a 0-10 narrative fit score."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="RNDR",
            token_description="GPU rendering network",
            active_narratives=sample_narratives,
        )

        assert 0.0 <= result.narrative_fit_score <= 10.0

    @pytest.mark.asyncio
    async def test_score_calculates_narrative_momentum(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should calculate aggregate momentum of aligned narratives."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="RNDR",
            token_description="GPU rendering network",
            active_narratives=sample_narratives,
        )

        assert 0.0 <= result.narrative_momentum <= 10.0

    @pytest.mark.asyncio
    async def test_score_handles_no_aligned_narratives(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should handle tokens not in any narrative."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="UNKNOWN",
            token_description="Some obscure token",
            active_narratives=sample_narratives,
        )

        assert result.narrative_fit_score >= 0.0  # Should still return valid score
        assert result.strongest_narrative == ""  # No strongest narrative

    @pytest.mark.asyncio
    async def test_score_handles_empty_narratives(self) -> None:
        """score should handle empty narratives list."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        result = await scorer.score(
            token_symbol="BTC",
            token_description="Bitcoin",
            active_narratives=NarrativeDetectorResult(narratives=[]),
        )

        assert result.narrative_fit_score == 0.0
        assert result.aligned_narratives == []
        assert result.strongest_narrative == ""

    @pytest.mark.asyncio
    async def test_score_weights_by_narrative_momentum(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score should weight by narrative momentum score."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        # FET is only in AI + Blockchain (momentum 8.5)
        result = await scorer.score(
            token_symbol="FET",
            token_description="AI agent network",
            active_narratives=sample_narratives,
        )

        # With high momentum AI narrative, score should be decent
        assert result.narrative_fit_score > 0.0


class TestNarrativeScorerBatchScore:
    """Tests for batch scoring."""

    @pytest.fixture
    def sample_narratives(self) -> NarrativeDetectorResult:
        """Sample narratives for testing."""
        return NarrativeDetectorResult(
            narratives=[
                Narrative(
                    name="AI + Blockchain",
                    momentum_score=8.5,
                    trend="accelerating",
                    tokens=["FET", "RNDR"],
                    keywords=["AI"],
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_score_batch_returns_list(
        self, sample_narratives: NarrativeDetectorResult
    ) -> None:
        """score_batch should return list of results."""
        provider = LLMProvider()
        scorer = NarrativeScorer(llm_provider=provider)

        tokens = [
            {"symbol": "FET", "description": "AI network"},
            {"symbol": "RNDR", "description": "GPU network"},
        ]

        results = await scorer.score_batch(tokens, sample_narratives)

        assert len(results) == 2
        assert all(isinstance(r, NarrativeScoreResult) for r in results)
