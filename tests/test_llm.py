import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.agents.base import (
    AnthropicClient,
    OpenAIClient,
    GeminiClient,
    get_llm_client,
)
from backend.core.enums import LLMProvider


def test_get_llm_client_anthropic():
    with patch("backend.agents.base.anthropic"):
        client = get_llm_client(LLMProvider.ANTHROPIC)
        assert isinstance(client, AnthropicClient)


def test_get_llm_client_openai():
    with patch("backend.agents.base.openai"):
        client = get_llm_client(LLMProvider.OPENAI)
        assert isinstance(client, OpenAIClient)


def test_get_llm_client_gemini():
    with patch("backend.agents.base.genai"):
        client = get_llm_client(LLMProvider.GEMINI)
        assert isinstance(client, GeminiClient)
