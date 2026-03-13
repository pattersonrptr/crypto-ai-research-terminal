"""Tests for SummaryGenerator — TDD [RED] phase."""

from unittest.mock import AsyncMock

import pytest

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.summary_generator import ProjectSummary, SummaryGenerator


class TestProjectSummary:
    """Tests for ProjectSummary dataclass."""

    def test_project_summary_has_required_fields(self) -> None:
        """ProjectSummary should have all required fields."""
        summary = ProjectSummary(
            summary_text="A plain language summary",
            key_strengths=["strength1", "strength2"],
            key_risks=["risk1", "risk2"],
            investment_thesis="Why it might be interesting",
            target_audience="Who would be interested",
        )
        assert summary.summary_text == "A plain language summary"
        assert len(summary.key_strengths) == 2
        assert len(summary.key_risks) == 2
        assert summary.investment_thesis == "Why it might be interesting"
        assert summary.target_audience == "Who would be interested"


class TestSummaryGeneratorInit:
    """Tests for SummaryGenerator initialization."""

    def test_init_requires_llm_provider(self) -> None:
        """Should accept an LLMProvider instance."""
        provider = LLMProvider()
        generator = SummaryGenerator(llm_provider=provider)
        assert generator.llm_provider is provider

    def test_init_accepts_max_words(self) -> None:
        """Should accept configurable max words."""
        provider = LLMProvider()
        generator = SummaryGenerator(llm_provider=provider, max_words=500)
        assert generator.max_words == 500

    def test_init_default_max_words(self) -> None:
        """Default max words should be 300."""
        provider = LLMProvider()
        generator = SummaryGenerator(llm_provider=provider)
        assert generator.max_words == 300


class TestSummaryGeneratorGenerate:
    """Tests for SummaryGenerator generate method."""

    @pytest.fixture
    def mock_llm_response(self) -> LLMResponse:
        """Mock LLM response for summary generation."""
        return LLMResponse(
            text="""{
                "summary_text": "Celestia is a modular blockchain.",
                "key_strengths": ["First mover in modular space", "Strong team"],
                "key_risks": ["Competition from Ethereum", "Token concerns"],
                "investment_thesis": "Bet on modular blockchain narrative growth.",
                "target_audience": "Technical investors interested in infrastructure."
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=200,
        )

    @pytest.mark.asyncio
    async def test_generate_returns_project_summary(self, mock_llm_response: LLMResponse) -> None:
        """generate should return ProjectSummary."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        generator = SummaryGenerator(llm_provider=provider)
        result = await generator.generate(
            name="Celestia",
            description="A modular blockchain",
            market_data={"price": 10.5, "market_cap": 1_000_000_000},
        )

        assert isinstance(result, ProjectSummary)
        assert "Celestia" in result.summary_text or "modular" in result.summary_text

    @pytest.mark.asyncio
    async def test_generate_includes_market_data_in_prompt(
        self, mock_llm_response: LLMResponse
    ) -> None:
        """generate should include market data in LLM prompt."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        generator = SummaryGenerator(llm_provider=provider)
        await generator.generate(
            name="Test",
            description="Test desc",
            market_data={"price": 100.0, "volume_24h": 50_000_000},
        )

        provider.generate.assert_called_once()
        call_args = provider.generate.call_args
        prompt = call_args[0][0]
        assert "100" in prompt or "price" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_includes_scores_in_prompt(self, mock_llm_response: LLMResponse) -> None:
        """generate should include scores in LLM prompt."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        generator = SummaryGenerator(llm_provider=provider)
        await generator.generate(
            name="Test",
            description="Test desc",
            scores={"fundamental_score": 7.5, "growth_score": 8.0},
        )

        call_args = provider.generate.call_args
        prompt = call_args[0][0]
        assert "7.5" in prompt or "fundamental" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_returns_key_strengths(self, mock_llm_response: LLMResponse) -> None:
        """generate should return key strengths."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        generator = SummaryGenerator(llm_provider=provider)
        result = await generator.generate(
            name="Test",
            description="Test",
        )

        assert len(result.key_strengths) > 0
        assert "First mover" in result.key_strengths[0]

    @pytest.mark.asyncio
    async def test_generate_returns_key_risks(self, mock_llm_response: LLMResponse) -> None:
        """generate should return key risks."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        generator = SummaryGenerator(llm_provider=provider)
        result = await generator.generate(
            name="Test",
            description="Test",
        )

        assert len(result.key_risks) > 0

    @pytest.mark.asyncio
    async def test_generate_handles_malformed_json(self) -> None:
        """generate should handle malformed JSON from LLM."""
        provider = LLMProvider()
        response = LLMResponse(
            text="Not valid JSON",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        generator = SummaryGenerator(llm_provider=provider)
        with pytest.raises(ValueError, match="Failed to parse"):
            await generator.generate(name="Test", description="Test")


class TestSummaryGeneratorPlainText:
    """Tests for plain text summary generation."""

    @pytest.fixture
    def mock_plain_text_response(self) -> LLMResponse:
        """Mock LLM response for plain text generation."""
        return LLMResponse(
            text="Celestia is a blockchain that solves a serious technical problem.",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )

    @pytest.mark.asyncio
    async def test_generate_plain_text_returns_string(
        self, mock_plain_text_response: LLMResponse
    ) -> None:
        """generate_plain_text should return simple string summary."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_plain_text_response)

        generator = SummaryGenerator(llm_provider=provider)
        result = await generator.generate_plain_text(
            name="Celestia",
            description="A modular blockchain",
        )

        assert isinstance(result, str)
        assert "Celestia" in result or "blockchain" in result

    @pytest.mark.asyncio
    async def test_generate_plain_text_respects_max_words(
        self, mock_plain_text_response: LLMResponse
    ) -> None:
        """generate_plain_text should mention max_words in prompt."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_plain_text_response)

        generator = SummaryGenerator(llm_provider=provider, max_words=150)
        await generator.generate_plain_text(
            name="Test",
            description="Test",
        )

        call_args = provider.generate.call_args
        prompt = call_args[0][0]
        # Check that max words is mentioned in prompt
        assert "150" in prompt or "words" in prompt.lower()
