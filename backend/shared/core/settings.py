# backend/core/settings.py
"""Application settings and configuration."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings

from .enums import LLMProvider, MarketDataProvider


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    litellm_url: str = "http://litellm:4000"  # Service URL in Docker
    anthropic_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    google_api_key: SecretStr = SecretStr("")

    # LangFuse Configuration
    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_host: str | None = None

    # Market Data Configuration
    market_data_provider: MarketDataProvider = MarketDataProvider.YAHOO
    alpha_vantage_api_key: SecretStr = SecretStr("")

    # Search Configuration
    exa_api_key: SecretStr = SecretStr("")

    # Authentication Configuration
    jwt_secret: SecretStr = SecretStr("")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_encryption_key: SecretStr = SecretStr("")

    # LangFuse Extras
    langfuse_secret: SecretStr = SecretStr("")
    langfuse_salt: SecretStr = SecretStr("")

    # MinIO Configuration
    minio_root_user: str = "minio"
    minio_root_password: SecretStr = SecretStr("minio123")

    # Database Configuration
    database_url: str = "postgresql+asyncpg://localhost/boardroom"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"

    # Email Configuration (SendGrid)
    sendgrid_api_key: SecretStr = SecretStr("")
    sendgrid_from_email: str = "noreply@boardroom.app"
    sendgrid_from_name: str = "Boardroom"
    email_notifications_enabled: bool = False

    # CORS Configuration
    cors_origins: str = (
        "http://localhost:5173"  # Comma-separated list of allowed origins
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()
