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
    # IMPORTANT: These secrets must be set in your .env file.
    # You can generate a strong JWT_SECRET using: openssl rand -hex 32
    # You can generate a Fernet key for API_KEY_ENCRYPTION_KEY in a Python shell:
    # >>> from cryptography.fernet import Fernet
    # >>> Fernet.generate_key().decode()
    jwt_secret: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_encryption_key: str  # A URL-safe base64-encoded 32-byte key

    # Database Configuration
    database_url: str = "postgresql+asyncpg://localhost/boardroom"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"

    # Email Configuration (SendGrid)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@boardroom.app"
    sendgrid_from_name: str = "Boardroom"
    email_notifications_enabled: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()
