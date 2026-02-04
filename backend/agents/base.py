from abc import ABC, abstractmethod
from typing import Any

import anthropic
import google.generativeai as genai
import openai

from backend.config import LLMProvider, settings


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        pass

    @abstractmethod
    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        pass


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = model

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
            tools=tools,
        )
        for block in response.content:
            if block.type == "tool_use":
                return {"tool": block.name, "args": block.input}
        return {"text": response.content[0].text}


class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str = "gpt-4o"):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        openai_tools = [
            {"type": "function", "function": t} for t in tools
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            import json
            return {"tool": tc.function.name, "args": json.loads(tc.function.arguments)}
        return {"text": msg.content or ""}


class GeminiClient(BaseLLMClient):
    def __init__(self, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(model)

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
        response = await self.model.generate_content_async(contents)
        return response.text

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        # Gemini tool calling - simplified
        response = await self.complete(messages)
        return {"text": response}


def get_llm_client(provider: LLMProvider | None = None) -> BaseLLMClient:
    provider = provider or settings.llm_provider
    match provider:
        case LLMProvider.ANTHROPIC:
            return AnthropicClient()
        case LLMProvider.OPENAI:
            return OpenAIClient()
        case LLMProvider.GEMINI:
            return GeminiClient()
