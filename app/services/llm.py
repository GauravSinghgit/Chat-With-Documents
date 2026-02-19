from groq import Groq, AsyncGroq
from app.config import settings
from app.utils.logger import logger
from typing import AsyncGenerator


class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.async_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL

    async def generate(self, prompt: str) -> str:
        """Standard single-response generation. Raises on error — callers must handle."""
        completion = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_RESPONSE_TOKENS,
        )
        return completion.choices[0].message.content

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streaming token-by-token generation via SSE."""
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_RESPONSE_TOKENS,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield "Sorry, I encountered an error. Please try again."
