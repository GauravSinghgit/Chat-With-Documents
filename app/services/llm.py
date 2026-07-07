from collections.abc import AsyncGenerator
from typing import Any

from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.config import settings
from app.utils.logger import logger


def as_text(content: str | list[str | dict]) -> str:
    """BaseMessage.content is typed to support multi-part (e.g. multimodal)
    responses; a text-only Groq chat model always returns a plain string."""
    return content if isinstance(content, str) else "".join(str(part) for part in content)


class LLMService:
    """Thin wrapper around ChatGroq exposing the single-response and
    streaming interfaces the rest of the app depends on."""

    def __init__(self) -> None:
        self.client = ChatGroq(
            model=settings.MODEL,
            api_key=SecretStr(settings.GROQ_API_KEY),
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_RESPONSE_TOKENS,
        )

    async def generate(self, prompt: str) -> str:
        """Standard single-response generation."""
        try:
            response = await self.client.ainvoke(prompt)
            return as_text(response.content)
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return "I encountered an error generating a response. Please try again."

    async def generate_with_usage(self, prompt: str) -> tuple[str, dict[str, int]]:
        """Single-response generation that also returns token usage, for the
        usage-analytics dashboard (app/api/admin.py)."""
        try:
            response = await self.client.ainvoke(prompt)
            usage: dict[str, Any] = dict(response.usage_metadata or {})
            return as_text(response.content), {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            }
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return "I encountered an error generating a response. Please try again.", {}

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streaming token-by-token generation via SSE."""
        try:
            async for chunk in self.client.astream(prompt):
                if chunk.content:
                    yield as_text(chunk.content)
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield "Sorry, I encountered an error. Please try again."
