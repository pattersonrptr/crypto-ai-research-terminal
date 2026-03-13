"""Tests for ProjectClassifier — TDD [RED] phase."""

from unittest.mock import AsyncMock

import pytest

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.project_classifier import ProjectCategory, ProjectClassifier


class TestProjectCategory:
    """Tests for ProjectCategory enum."""

    def test_project_category_has_all_categories(self) -> None:
        """ProjectCategory should have all expected categories."""
        expected = {
            "LAYER1",
            "LAYER2",
            "DEFI",
            "AI",
            "GAMING",
            "INFRASTRUCTURE",
            "DEPIN",
            "ORACLE",
            "PRIVACY",
            "MEMECOIN",
            "RWA",
            "RESTAKING",
        }
        actual = {cat.name for cat in ProjectCategory}
        assert expected == actual


class TestProjectClassifierInit:
    """Tests for ProjectClassifier initialization."""

    def test_init_requires_llm_provider(self) -> None:
        """Should accept an LLMProvider instance."""
        provider = LLMProvider()
        classifier = ProjectClassifier(llm_provider=provider)
        assert classifier.llm_provider is provider


class TestProjectClassifierClassify:
    """Tests for ProjectClassifier classify method."""

    @pytest.fixture
    def mock_llm_response(self) -> LLMResponse:
        """Mock LLM response for classification."""
        return LLMResponse(
            text="""{
                "primary_category": "LAYER1",
                "secondary_categories": ["INFRASTRUCTURE"],
                "confidence": 0.95
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )

    @pytest.mark.asyncio
    async def test_classify_returns_primary_category(self, mock_llm_response: LLMResponse) -> None:
        """classify should return primary category."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        classifier = ProjectClassifier(llm_provider=provider)
        result = await classifier.classify(
            name="Solana",
            description="High-performance blockchain",
        )

        assert result.primary_category == ProjectCategory.LAYER1

    @pytest.mark.asyncio
    async def test_classify_returns_secondary_categories(
        self, mock_llm_response: LLMResponse
    ) -> None:
        """classify should return secondary categories."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        classifier = ProjectClassifier(llm_provider=provider)
        result = await classifier.classify(
            name="Solana",
            description="High-performance blockchain",
        )

        assert ProjectCategory.INFRASTRUCTURE in result.secondary_categories

    @pytest.mark.asyncio
    async def test_classify_returns_confidence(self, mock_llm_response: LLMResponse) -> None:
        """classify should return confidence score."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        classifier = ProjectClassifier(llm_provider=provider)
        result = await classifier.classify(
            name="Solana",
            description="High-performance blockchain",
        )

        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_classify_passes_project_info_to_llm(
        self, mock_llm_response: LLMResponse
    ) -> None:
        """classify should pass project info to LLM."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)

        classifier = ProjectClassifier(llm_provider=provider)
        await classifier.classify(
            name="Test Project",
            description="A test project description",
        )

        provider.generate.assert_called_once()
        call_args = provider.generate.call_args
        prompt = call_args[0][0]
        assert "Test Project" in prompt
        assert "A test project description" in prompt

    @pytest.mark.asyncio
    async def test_classify_handles_defi_project(self) -> None:
        """classify should correctly identify DeFi project."""
        provider = LLMProvider()
        response = LLMResponse(
            text="""{
                "primary_category": "DEFI",
                "secondary_categories": [],
                "confidence": 0.9
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        classifier = ProjectClassifier(llm_provider=provider)
        result = await classifier.classify(
            name="Uniswap",
            description="Decentralized exchange protocol",
        )

        assert result.primary_category == ProjectCategory.DEFI

    @pytest.mark.asyncio
    async def test_classify_handles_ai_project(self) -> None:
        """classify should correctly identify AI project."""
        provider = LLMProvider()
        response = LLMResponse(
            text="""{
                "primary_category": "AI",
                "secondary_categories": ["INFRASTRUCTURE"],
                "confidence": 0.85
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        classifier = ProjectClassifier(llm_provider=provider)
        result = await classifier.classify(
            name="Fetch.ai",
            description="Decentralized AI network",
        )

        assert result.primary_category == ProjectCategory.AI

    @pytest.mark.asyncio
    async def test_classify_handles_unknown_category(self) -> None:
        """classify should handle invalid category from LLM."""
        provider = LLMProvider()
        response = LLMResponse(
            text="""{
                "primary_category": "INVALID_CATEGORY",
                "secondary_categories": [],
                "confidence": 0.5
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        classifier = ProjectClassifier(llm_provider=provider)
        with pytest.raises(ValueError, match="Unknown category"):
            await classifier.classify(
                name="Unknown",
                description="Some project",
            )

    @pytest.mark.asyncio
    async def test_classify_handles_malformed_json(self) -> None:
        """classify should handle malformed JSON from LLM."""
        provider = LLMProvider()
        response = LLMResponse(
            text="Not valid JSON",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        classifier = ProjectClassifier(llm_provider=provider)
        with pytest.raises(ValueError, match="Failed to parse"):
            await classifier.classify(
                name="Test",
                description="Test",
            )


class TestProjectClassifierBatchClassify:
    """Tests for batch classification."""

    @pytest.mark.asyncio
    async def test_classify_batch_returns_list(self) -> None:
        """classify_batch should return list of results."""
        provider = LLMProvider()
        response = LLMResponse(
            text="""{
                "primary_category": "LAYER1",
                "secondary_categories": [],
                "confidence": 0.9
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )
        provider.generate = AsyncMock(return_value=response)

        classifier = ProjectClassifier(llm_provider=provider)
        projects = [
            {"name": "Solana", "description": "High-performance blockchain"},
            {"name": "Ethereum", "description": "Smart contract platform"},
        ]

        results = await classifier.classify_batch(projects)

        assert len(results) == 2
        assert all(r.primary_category == ProjectCategory.LAYER1 for r in results)
