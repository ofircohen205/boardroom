from abc import ABC, abstractmethod
from typing import Any

from backend.shared.core.enums import LLMProvider
from backend.shared.core.settings import settings


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

    @abstractmethod
    async def complete_structured(
        self, messages: list[dict], json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Complete with structured JSON output based on schema."""
        pass


from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


class LiteLLMClient(BaseLLMClient):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = AsyncOpenAI(
            api_key="sk-1234",  # pragma: allowlist secret  # LiteLLM Proxy placeholder, not checked unless master key is set
            base_url=settings.litellm_url,
        )

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        from typing import cast

        # OpenAI SDK expects tools in a specific format if provided
        openai_tools = None
        if tools:
            openai_tools = [{"type": "function", "function": t} for t in tools]

        kwargs = {}
        if openai_tools:
            kwargs["tools"] = cast(Any, openai_tools)

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=cast(list[ChatCompletionMessageParam], messages),
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        from typing import cast

        openai_tools = [{"type": "function", "function": t} for t in tools]

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=cast(list[ChatCompletionMessageParam], messages),
            tools=cast(list[ChatCompletionToolParam], openai_tools),
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            import json

            tc = msg.tool_calls[0]
            if tc.type == "function":
                function_args = json.loads(tc.function.arguments)
                return {"tool": tc.function.name, "args": function_args}

        return {"text": msg.content or ""}

    async def complete_structured(
        self, messages: list[dict], json_schema: dict[str, Any]
    ) -> dict[str, Any]:
        import json
        from typing import cast

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=cast(list[ChatCompletionMessageParam], messages),
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "strict": True,
                    "schema": json_schema,
                },
            },
        )
        content = response.choices[0].message.content
        return json.loads(content) if content else {}


def get_llm_client(provider: LLMProvider | None = None) -> BaseLLMClient:
    provider = provider or settings.llm_provider

    # Map provider to logical model name defined in litellm_config.yaml
    match provider:
        case LLMProvider.ANTHROPIC:
            model = "sonnet"
        case LLMProvider.OPENAI:
            model = "gpt-4o"
        case LLMProvider.GEMINI:
            model = "gemini-flash"
        case _:
            model = "gpt-4o"

    return LiteLLMClient(model_name=model)
