"""Tests for NarrativeDetector — TDD [RED] phase."""

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.narrative_detector import (
    Narrative,
    NarrativeDetector,
    NarrativeDetectorResult,
)


class TestNarrativeDataclasses:
    """Tests for Narrative dataclasses."""

    def test_narrative_has_required_fields(self) -> None:
        """Narrative should have all required fields."""
        narrative = Narrative(
            name="AI + Blockchain",
            momentum_score=8.7,
            trend="accelerating",
            tokens=["FET", "RNDR", "TAO"],
            keywords=["AI agents", "GPU compute"],
        )
        assert narrative.name == "AI + Blockchain"
        assert narrative.momentum_score == 8.7
        assert narrative.trend == "accelerating"
        assert narrative.tokens == ["FET", "RNDR", "TAO"]
        assert narrative.keywords == ["AI agents", "GPU compute"]

    def test_narrative_detector_result_has_narratives_list(self) -> None:
        """NarrativeDetectorResult should contain list of narratives."""
        narrative = Narrative(
            name="Test",
            momentum_score=5.0,
            trend="stable",
            tokens=["BTC"],
            keywords=["test"],
        )
        result = NarrativeDetectorResult(narratives=[narrative])
        assert len(result.narratives) == 1
        assert result.narratives[0].name == "Test"


class TestNarrativeDetectorInit:
    """Tests for NarrativeDetector initialization."""

    def test_init_requires_llm_provider(self) -> None:
        """Should accept an LLMProvider instance."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)
        assert detector.llm_provider is provider

    def test_init_accepts_min_cluster_size(self) -> None:
        """Should accept configurable minimum cluster size."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider, min_cluster_size=10)
        assert detector.min_cluster_size == 10

    def test_init_default_min_cluster_size(self) -> None:
        """Default minimum cluster size should be 5."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)
        assert detector.min_cluster_size == 5


class TestNarrativeDetectorDetect:
    """Tests for NarrativeDetector detect method."""

    @pytest.fixture
    def sample_posts(self) -> list[dict]:
        """Sample social media posts for testing."""
        return [
            {"text": "AI agents on blockchain are the future! $FET $RNDR", "source": "twitter"},
            {"text": "GPU compute networks are taking off $RNDR", "source": "twitter"},
            {"text": "Decentralized AI is the next big thing $TAO", "source": "reddit"},
            {"text": "Layer 2s are scaling Ethereum $ARB $OP", "source": "twitter"},
            {"text": "Optimism upgrade coming soon $OP", "source": "reddit"},
        ]

    @pytest.fixture
    def mock_llm_response(self) -> LLMResponse:
        """Mock LLM response for narrative labeling."""
        return LLMResponse(
            text="""{
                "name": "AI + Blockchain",
                "keywords": ["AI agents", "GPU compute", "decentralized AI"]
            }""",
            provider="ollama",
            model="llama3.2",
            tokens_used=100,
        )

    @pytest.mark.asyncio
    async def test_detect_returns_narrative_detector_result(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should return NarrativeDetectorResult."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed = AsyncMock(return_value=[0.1] * 384)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        # Mock clustering to return predetermined clusters
        with patch.object(detector, "_cluster_embeddings", return_value=[0, 0, 0, 1, 1]):
            result = await detector.detect(sample_posts)

        assert isinstance(result, NarrativeDetectorResult)
        assert len(result.narratives) > 0

    @pytest.mark.asyncio
    async def test_detect_creates_embeddings_for_posts(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should create embeddings for all posts."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        with patch.object(detector, "_cluster_embeddings", return_value=[0] * len(sample_posts)):
            await detector.detect(sample_posts)

        provider.embed_batch.assert_called_once()
        texts = provider.embed_batch.call_args[0][0]
        assert len(texts) == len(sample_posts)

    @pytest.mark.asyncio
    async def test_detect_uses_llm_to_label_clusters(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should use LLM to generate narrative names and keywords."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        with patch.object(detector, "_cluster_embeddings", return_value=[0, 0, 0, 1, 1]):
            await detector.detect(sample_posts)

        # LLM should be called for each cluster (2 clusters)
        assert provider.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_detect_extracts_tokens_from_posts(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should extract mentioned tokens from cluster posts."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        # Put all AI posts in cluster 0
        with patch.object(detector, "_cluster_embeddings", return_value=[0, 0, 0, 1, 1]):
            result = await detector.detect(sample_posts)

        # Find AI narrative
        ai_narrative = next(n for n in result.narratives if n.name == "AI + Blockchain")
        # Should extract tokens mentioned with $ prefix
        assert "FET" in ai_narrative.tokens or "RNDR" in ai_narrative.tokens

    @pytest.mark.asyncio
    async def test_detect_calculates_momentum_score(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should calculate momentum score for each narrative."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        with patch.object(detector, "_cluster_embeddings", return_value=[0, 0, 0, 1, 1]):
            result = await detector.detect(sample_posts)

        for narrative in result.narratives:
            assert 0.0 <= narrative.momentum_score <= 10.0

    @pytest.mark.asyncio
    async def test_detect_determines_trend_direction(
        self, sample_posts: list[dict], mock_llm_response: LLMResponse
    ) -> None:
        """detect should determine trend direction for each narrative."""
        provider = LLMProvider()
        provider.generate = AsyncMock(return_value=mock_llm_response)
        provider.embed_batch = AsyncMock(return_value=[[0.1] * 384] * len(sample_posts))

        detector = NarrativeDetector(llm_provider=provider)

        with patch.object(detector, "_cluster_embeddings", return_value=[0, 0, 0, 1, 1]):
            result = await detector.detect(sample_posts)

        valid_trends = {"accelerating", "stable", "declining"}
        for narrative in result.narratives:
            assert narrative.trend in valid_trends


class TestNarrativeDetectorClustering:
    """Tests for clustering functionality."""

    def test_cluster_embeddings_returns_labels(self) -> None:
        """_cluster_embeddings should return cluster labels."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)

        # Create mock embeddings (5 samples, 384 dimensions)
        embeddings = [[float(i + j) for j in range(384)] for i in range(5)]

        labels = detector._cluster_embeddings(embeddings)

        assert len(labels) == 5
        assert all(isinstance(label, int) for label in labels)

    def test_cluster_embeddings_filters_noise(self) -> None:
        """_cluster_embeddings should handle noise points (label -1)."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)

        # With very sparse data, some points may be noise
        embeddings = [[float(i * 100)] * 384 for i in range(10)]

        labels = detector._cluster_embeddings(embeddings)

        # Should return labels for all points (including -1 for noise)
        assert len(labels) == 10


class TestNarrativeDetectorTokenExtraction:
    """Tests for token extraction from posts."""

    def test_extract_tokens_finds_dollar_prefixed_tokens(self) -> None:
        """_extract_tokens should find $TOKEN mentions."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)

        posts = [
            {"text": "Bullish on $BTC and $ETH today!", "source": "twitter"},
            {"text": "$SOL is looking good", "source": "reddit"},
        ]

        tokens = detector._extract_tokens(posts)

        assert "BTC" in tokens
        assert "ETH" in tokens
        assert "SOL" in tokens

    def test_extract_tokens_handles_lowercase(self) -> None:
        """_extract_tokens should handle lowercase tokens."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)

        posts = [{"text": "$btc and $eth", "source": "twitter"}]

        tokens = detector._extract_tokens(posts)

        assert "BTC" in tokens
        assert "ETH" in tokens

    def test_extract_tokens_deduplicates(self) -> None:
        """_extract_tokens should deduplicate tokens."""
        provider = LLMProvider()
        detector = NarrativeDetector(llm_provider=provider)

        posts = [
            {"text": "$BTC $BTC $BTC", "source": "twitter"},
            {"text": "$BTC again", "source": "reddit"},
        ]

        tokens = detector._extract_tokens(posts)

        assert tokens.count("BTC") == 1
