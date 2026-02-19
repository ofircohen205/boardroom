# tests/unit/analysis/test_llm_client.py
"""
Unit tests for backend/shared/ai/agents/base.py.

Tests cover:
- LiteLLMClient.complete: basic response, tools kwarg forwarding, None-content fallback
- LiteLLMClient.complete_with_tools: tool-call path, text-only path
- LiteLLMClient.complete_structured: JSON parsing, None-content fallback
- get_llm_client: return type and model name mapping for all providers
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.shared.ai.agents.base import LiteLLMClient, get_llm_client
from backend.shared.core.enums import LLMProvider

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openai_client():
    """A bare AsyncMock that stands in for the AsyncOpenAI instance."""
    return AsyncMock()


@pytest.fixture
def llm_client(mock_openai_client):
    """LiteLLMClient with its internal AsyncOpenAI client replaced by a mock."""
    client = LiteLLMClient(model_name="test-model")
    client.client = mock_openai_client
    return client


def _make_response(content=None, tool_calls=None):
    """Build a minimal mock ChatCompletion response."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls

    response = MagicMock()
    response.choices[0].message = msg
    return response


# ---------------------------------------------------------------------------
# LiteLLMClient.complete
# ---------------------------------------------------------------------------


async def test_complete_returns_message_content(llm_client, mock_openai_client):
    """complete() returns the content string from the first choice."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response("Hello world")
    )

    result = await llm_client.complete([{"role": "user", "content": "Hi"}])

    assert result == "Hello world"


async def test_complete_returns_empty_string_when_content_none(
    llm_client, mock_openai_client
):
    """complete() returns '' when the message content is None."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(None)
    )

    result = await llm_client.complete([{"role": "user", "content": "Hi"}])

    assert result == ""


async def test_complete_without_tools_does_not_pass_tools_kwarg(
    llm_client, mock_openai_client
):
    """complete() called without tools must not include 'tools' in the API call."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response("ok")
    )

    await llm_client.complete([{"role": "user", "content": "test"}])

    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    assert "tools" not in call_kwargs


async def test_complete_with_tools_passes_tools_kwarg(llm_client, mock_openai_client):
    """complete() called with tools must forward them wrapped with type=function."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response("response")
    )

    tools = [{"name": "search", "description": "search the web"}]
    await llm_client.complete([{"role": "user", "content": "test"}], tools=tools)

    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    assert "tools" in call_kwargs
    assert call_kwargs["tools"][0]["type"] == "function"
    assert call_kwargs["tools"][0]["function"] == tools[0]


async def test_complete_calls_api_with_correct_model(llm_client, mock_openai_client):
    """complete() passes model_name to the API."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response("ok")
    )

    await llm_client.complete([{"role": "user", "content": "test"}])

    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "test-model"


# ---------------------------------------------------------------------------
# LiteLLMClient.complete_with_tools
# ---------------------------------------------------------------------------


async def test_complete_with_tools_returns_tool_call(llm_client, mock_openai_client):
    """complete_with_tools() returns {tool, args} when the model calls a tool."""
    mock_tc = MagicMock()
    mock_tc.type = "function"
    mock_tc.function.name = "search"
    mock_tc.function.arguments = json.dumps({"query": "AAPL"})

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(content=None, tool_calls=[mock_tc])
    )

    result = await llm_client.complete_with_tools(
        [{"role": "user", "content": "search AAPL"}],
        tools=[{"name": "search", "description": "search tool"}],
    )

    assert result == {"tool": "search", "args": {"query": "AAPL"}}


async def test_complete_with_tools_returns_text_when_no_tool_calls(
    llm_client, mock_openai_client
):
    """complete_with_tools() returns {text: ...} when the model responds in text."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response("Here is some text", tool_calls=None)
    )

    result = await llm_client.complete_with_tools(
        [{"role": "user", "content": "explain"}],
        tools=[{"name": "search"}],
    )

    assert result == {"text": "Here is some text"}


async def test_complete_with_tools_empty_text_when_content_none_and_no_calls(
    llm_client, mock_openai_client
):
    """complete_with_tools() returns {text: ''} when content is None and no tool calls."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(None, tool_calls=None)
    )

    result = await llm_client.complete_with_tools(
        [{"role": "user", "content": "test"}],
        tools=[{"name": "search"}],
    )

    assert result == {"text": ""}


# ---------------------------------------------------------------------------
# LiteLLMClient.complete_structured
# ---------------------------------------------------------------------------


async def test_complete_structured_parses_json(llm_client, mock_openai_client):
    """complete_structured() deserialises the content string into a dict."""
    payload = {"action": "BUY", "confidence": 0.9}
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(json.dumps(payload))
    )

    schema = {"type": "object", "properties": {"action": {"type": "string"}}}
    result = await llm_client.complete_structured(
        [{"role": "user", "content": "analyze AAPL"}], schema
    )

    assert result == payload


async def test_complete_structured_returns_empty_dict_when_content_none(
    llm_client, mock_openai_client
):
    """complete_structured() returns {} when content is None."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(None)
    )

    result = await llm_client.complete_structured([], {})

    assert result == {}


async def test_complete_structured_passes_json_schema_in_response_format(
    llm_client, mock_openai_client
):
    """complete_structured() embeds json_schema inside response_format."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_response(json.dumps({"ok": True}))
    )

    schema = {"type": "object"}
    await llm_client.complete_structured([{"role": "user", "content": "test"}], schema)

    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    rf = call_kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"] == schema
    assert rf["json_schema"]["strict"] is True


# ---------------------------------------------------------------------------
# get_llm_client
# ---------------------------------------------------------------------------


def test_get_llm_client_returns_litellm_client():
    """get_llm_client() with no args returns a LiteLLMClient."""
    client = get_llm_client()
    assert isinstance(client, LiteLLMClient)


def test_get_llm_client_anthropic_uses_sonnet_model():
    """get_llm_client(ANTHROPIC) selects the 'sonnet' logical model."""
    client = get_llm_client(LLMProvider.ANTHROPIC)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "sonnet"


def test_get_llm_client_openai_uses_gpt4o():
    """get_llm_client(OPENAI) selects 'gpt-4o'."""
    client = get_llm_client(LLMProvider.OPENAI)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "gpt-4o"


def test_get_llm_client_gemini_uses_flash():
    """get_llm_client(GEMINI) selects 'gemini-flash'."""
    client = get_llm_client(LLMProvider.GEMINI)
    assert isinstance(client, LiteLLMClient)
    assert client.model_name == "gemini-flash"
