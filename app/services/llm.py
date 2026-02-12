from groq import Groq
from app.config import settings


class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    async def generate(self, prompt: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_RESPONSE_TOKENS
            )

            return completion.choices[0].message.content

        except Exception as e:
            return f"Error generating response from Groq: {str(e)}"
