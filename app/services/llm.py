from typing import AsyncGenerator, Tuple

from langchain_groq import ChatGroq

from app.config import settings
from app.utils.logger import logger


class LLMService:
    """Thin wrapper around ChatGroq exposing the single-response and
    streaming interfaces the rest of the app depends on."""

    def __init__(self):
        self.client = ChatGroq(
            model=settings.MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_RESPONSE_TOKENS,
        )

    async def generate(self, prompt: str) -> str:
        """Standard single-response generation."""
        try:
            response = await self.client.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return "I encountered an error generating a response. Please try again."

    async def generate_with_usage(self, prompt: str) -> Tuple[str, dict]:
        """Single-response generation that also returns token usage, for the
        usage-analytics dashboard (app/api/admin.py)."""
        try:
            response = await self.client.ainvoke(prompt)
            usage = response.usage_metadata or {}
            return response.content, {
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
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield "Sorry, I encountered an error. Please try again."
