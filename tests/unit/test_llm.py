from backend.shared.ai.agents.base import (
    LiteLLMClient,
    get_llm_client,
)
from backend.shared.core.enums import LLMProvider


def test_get_llm_client_anthropic():
    client = get_llm_client(LLMProvider.ANTHROPIC)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "sonnet"


def test_get_llm_client_openai():
    client = get_llm_client(LLMProvider.OPENAI)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "gpt-4o"


def test_get_llm_client_gemini():
    client = get_llm_client(LLMProvider.GEMINI)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "gemini-flash"
