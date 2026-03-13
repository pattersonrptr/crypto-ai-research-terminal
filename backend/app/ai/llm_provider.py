"""LLMProvider — multi-provider LLM abstraction with automatic fallback.

Supports Ollama (local), Google Gemini, and OpenAI with configurable
fallback chain. Uses async HTTP calls for all providers.
"""

from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from app.config import settings
from app.exceptions import LLMProviderError

logger = structlog.get_logger(__name__)

VALID_PROVIDERS = {"ollama", "gemini", "openai"}


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    text: str
    provider: str
    model: str
    tokens_used: int


class LLMProvider:
    """Multi-provider LLM abstraction with automatic fallback.

    Tries providers in order: primary → fallback_chain[0] → fallback_chain[1] → ...
    Falls back to next provider when current one fails.
    """

    def __init__(
        self,
        primary: str = "ollama",
        fallback_chain: list[str] | None = None,
    ) -> None:
        """Initialize the LLM provider.

        Args:
            primary: Primary provider name (ollama, gemini, openai).
            fallback_chain: List of fallback provider names in order.

        Raises:
            ValueError: If any provider name is invalid.
        """
        if primary not in VALID_PROVIDERS:
            raise ValueError(f"Unknown provider: {primary}")

        if fallback_chain:
            for provider in fallback_chain:
                if provider not in VALID_PROVIDERS:
                    raise ValueError(f"Unknown provider: {provider}")

        self.primary = primary
        self.fallback_chain = fallback_chain or []
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LLMProvider":
        """Create HTTP client for provider calls."""
        self._client = httpx.AsyncClient(timeout=120.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate text using the configured LLM providers.

        Tries primary provider first, then falls back to others on failure.

        Args:
            prompt: User prompt to send to the LLM.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in response.

        Returns:
            LLMResponse with generated text and metadata.

        Raises:
            LLMProviderError: When all providers fail.
        """
        providers = [self.primary, *self.fallback_chain]
        errors: list[str] = []

        for provider in providers:
            try:
                log = logger.bind(provider=provider)
                log.debug("llm.generate.attempt")

                result = await self._call_provider(
                    provider, prompt, system_prompt, temperature, max_tokens
                )

                log.info("llm.generate.success", model=result.model)
                return result

            except Exception as e:
                errors.append(f"{provider}: {e}")
                logger.warning("llm.generate.failed", provider=provider, error=str(e))
                continue

        raise LLMProviderError(f"All LLM providers failed: {'; '.join(errors)}")

    async def _call_provider(
        self,
        provider: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Route to the appropriate provider method."""
        if provider == "ollama":
            return await self._call_ollama(prompt, system_prompt, temperature, max_tokens)
        elif provider == "gemini":
            return await self._call_gemini(prompt, system_prompt, temperature, max_tokens)
        elif provider == "openai":
            return await self._call_openai(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Call Ollama local LLM."""
        assert self._client is not None, "Use LLMProvider as async context manager"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            text=data["message"]["content"],
            provider="ollama",
            model=settings.ollama_model,
            tokens_used=data.get("eval_count", 0),
        )

    async def _call_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Call Google Gemini API."""
        assert self._client is not None, "Use LLMProvider as async context manager"

        if not settings.gemini_api_key:
            raise LLMProviderError("Gemini API key not configured")

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        response = await self._client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            params={"key": settings.gemini_api_key},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

        return LLMResponse(
            text=text,
            provider="gemini",
            model="gemini-pro",
            tokens_used=tokens,
        )

    async def _call_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Call OpenAI API."""
        assert self._client is not None, "Use LLMProvider as async context manager"

        if not settings.openai_api_key:
            raise LLMProviderError("OpenAI API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            provider="openai",
            model="gpt-4o",
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
        )

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for a single text.

        Uses sentence-transformers locally for embeddings.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        return await self._get_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        results = []
        for text in texts:
            embedding = await self._get_embedding(text)
            results.append(embedding)
        return results

    async def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding using sentence-transformers.

        Note: This is a placeholder. In production, we'd use the actual
        sentence-transformers library or an embedding API.
        """
        # Placeholder: return mock embedding
        # Real implementation would use sentence-transformers:
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # return model.encode(text).tolist()
        raise NotImplementedError("Embedding not yet implemented")
