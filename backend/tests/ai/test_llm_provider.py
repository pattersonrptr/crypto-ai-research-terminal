"""TDD tests for LLMProvider — multi-provider LLM abstraction with fallback."""

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.llm_provider import LLMProvider, LLMResponse


class TestLLMProviderInit:
    """Tests for LLMProvider initialization."""

    def test_init_defaults_to_ollama(self) -> None:
        """LLMProvider should default to Ollama as primary provider."""
        provider = LLMProvider()
        assert provider.primary == "ollama"

    def test_init_accepts_custom_primary(self) -> None:
        """LLMProvider should accept a custom primary provider."""
        provider = LLMProvider(primary="gemini")
        assert provider.primary == "gemini"

    def test_init_accepts_fallback_chain(self) -> None:
        """LLMProvider should accept a fallback chain."""
        provider = LLMProvider(primary="ollama", fallback_chain=["gemini", "openai"])
        assert provider.fallback_chain == ["gemini", "openai"]

    def test_init_validates_provider_names(self) -> None:
        """LLMProvider should raise ValueError for invalid provider names."""
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMProvider(primary="invalid_provider")


class TestLLMProviderGenerate:
    """Tests for LLMProvider.generate() method."""

    @pytest.mark.asyncio
    async def test_generate_returns_llm_response(self) -> None:
        """generate() should return an LLMResponse object."""
        provider = LLMProvider(primary="ollama")
        with patch.object(provider, "_call_ollama", new_callable=AsyncMock) as mock:
            mock.return_value = LLMResponse(
                text="Generated text",
                provider="ollama",
                model="llama3.2",
                tokens_used=50,
            )
            result = await provider.generate("Test prompt")

        assert isinstance(result, LLMResponse)
        assert result.text == "Generated text"
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_generate_uses_primary_provider_first(self) -> None:
        """generate() should try primary provider first."""
        provider = LLMProvider(primary="ollama", fallback_chain=["gemini"])
        with patch.object(provider, "_call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = LLMResponse(
                text="Ollama response",
                provider="ollama",
                model="llama3.2",
                tokens_used=30,
            )
            result = await provider.generate("Test prompt")

        mock_ollama.assert_called_once()
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_generate_falls_back_on_primary_failure(self) -> None:
        """generate() should use fallback when primary fails."""
        provider = LLMProvider(primary="ollama", fallback_chain=["gemini"])
        with (
            patch.object(provider, "_call_ollama", new_callable=AsyncMock) as mock_ollama,
            patch.object(provider, "_call_gemini", new_callable=AsyncMock) as mock_gemini,
        ):
            mock_ollama.side_effect = Exception("Ollama unavailable")
            mock_gemini.return_value = LLMResponse(
                text="Gemini response",
                provider="gemini",
                model="gemini-pro",
                tokens_used=40,
            )
            result = await provider.generate("Test prompt")

        mock_ollama.assert_called_once()
        mock_gemini.assert_called_once()
        assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_generate_tries_full_fallback_chain(self) -> None:
        """generate() should try all providers in fallback chain."""
        provider = LLMProvider(primary="ollama", fallback_chain=["gemini", "openai"])
        with (
            patch.object(provider, "_call_ollama", new_callable=AsyncMock) as mock_ollama,
            patch.object(provider, "_call_gemini", new_callable=AsyncMock) as mock_gemini,
            patch.object(provider, "_call_openai", new_callable=AsyncMock) as mock_openai,
        ):
            mock_ollama.side_effect = Exception("Ollama unavailable")
            mock_gemini.side_effect = Exception("Gemini unavailable")
            mock_openai.return_value = LLMResponse(
                text="OpenAI response",
                provider="openai",
                model="gpt-4o",
                tokens_used=60,
            )
            result = await provider.generate("Test prompt")

        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_generate_raises_when_all_providers_fail(self) -> None:
        """generate() should raise LLMProviderError when all providers fail."""
        from app.exceptions import LLMProviderError

        provider = LLMProvider(primary="ollama", fallback_chain=["gemini"])
        with (
            patch.object(provider, "_call_ollama", new_callable=AsyncMock) as mock_ollama,
            patch.object(provider, "_call_gemini", new_callable=AsyncMock) as mock_gemini,
        ):
            mock_ollama.side_effect = Exception("Ollama unavailable")
            mock_gemini.side_effect = Exception("Gemini unavailable")

            with pytest.raises(LLMProviderError, match="All LLM providers failed"):
                await provider.generate("Test prompt")


class TestLLMProviderEmbed:
    """Tests for LLMProvider.embed() method."""

    @pytest.mark.asyncio
    async def test_embed_returns_list_of_floats(self) -> None:
        """embed() should return a list of floats (embedding vector)."""
        provider = LLMProvider()
        with patch.object(provider, "_get_embedding", new_callable=AsyncMock) as mock:
            mock.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            result = await provider.embed("Test text")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_embed_batch_returns_list_of_embeddings(self) -> None:
        """embed_batch() should return embeddings for multiple texts."""
        provider = LLMProvider()
        with patch.object(provider, "_get_embedding", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
            ]
            result = await provider.embed_batch(["Text 1", "Text 2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_llm_response_has_required_fields(self) -> None:
        """LLMResponse should have text, provider, model, tokens_used."""
        response = LLMResponse(
            text="Hello",
            provider="ollama",
            model="llama3.2",
            tokens_used=10,
        )
        assert response.text == "Hello"
        assert response.provider == "ollama"
        assert response.model == "llama3.2"
        assert response.tokens_used == 10
