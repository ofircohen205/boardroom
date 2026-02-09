# backend/config.py
from enum import Enum
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class MarketDataProvider(str, Enum):
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"


class Settings(BaseSettings):
    # LLM
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Market Data
    market_data_provider: MarketDataProvider = MarketDataProvider.YAHOO
    alpha_vantage_api_key: str = ""

    # Search
    exa_api_key: str = ""

    # Auth
    jwt_secret: str = "secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_encryption_key: str = "a_very_secret_key_that_should_be_32_bytes"

    # Database
    database_url: str = "postgresql+asyncpg://localhost/boardroom"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
