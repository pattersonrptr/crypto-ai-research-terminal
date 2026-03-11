"""Custom exception classes for the application domain."""


class CryptoAIBaseError(Exception):
    """Base class for all application errors."""


class CollectorError(CryptoAIBaseError):
    """Raised when a data collector fails to retrieve data."""


class RateLimitError(CollectorError):
    """Raised when an external API rate limit is hit."""


class ScoringError(CryptoAIBaseError):
    """Raised when the scoring engine encounters an invalid state."""


class LLMProviderError(CryptoAIBaseError):
    """Raised when no LLM provider is available."""
