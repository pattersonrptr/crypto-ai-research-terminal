"""Centralized application settings loaded from .env via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/cryptoai"
    redis_url: str = "redis://localhost:6379"

    # API Keys
    coingecko_api_key: str = ""
    coinmarketcap_api_key: str = ""
    github_token: str = ""
    twitter_bearer_token: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # LLM provider
    llm_primary: str = "ollama"
    llm_fallback: str = "gemini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Analysis
    tokens_to_analyze: int = 300
    analysis_currency: str = "USD"
    coingecko_vs_currency: str = "usd"

    # Scheduler
    realtime_interval_minutes: int = 30
    daily_run_hour: int = 6
    weekly_run_day: str = "monday"
    monthly_run_day: int = 1

    # Alerts
    alert_listing_threshold: float = 0.70
    alert_whale_accumulation_threshold: float = 7.0
    alert_memecoin_social_growth: int = 500

    # Frontend
    vite_api_base_url: str = "http://localhost:8000"


settings = Settings()
