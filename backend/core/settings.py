# backend/core/settings.py
"""Application settings and configuration."""
from pydantic_settings import BaseSettings

from .enums import LLMProvider, MarketDataProvider


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Market Data Configuration
    market_data_provider: MarketDataProvider = MarketDataProvider.YAHOO
    alpha_vantage_api_key: str = ""

    # Search Configuration
    exa_api_key: str = ""

    # Authentication Configuration
    jwt_secret: str = "secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_encryption_key: str = "a_very_secret_key_that_should_be_32_bytes"

    # Database Configuration
    database_url: str = "postgresql+asyncpg://localhost/boardroom"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()
