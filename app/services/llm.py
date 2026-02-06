from huggingface_hub import InferenceClient
from app.config import settings


class LLMService:
    def __init__(self):
        self.client = InferenceClient(
            model=settings.HF_MODEL,
            token=settings.HF_API_KEY,
        )

    async def generate(self, prompt: str) -> str:
        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=settings.MAX_RESPONSE_TOKENS,
                temperature=settings.TEMPERATURE,
                return_full_text=False,
            )
            return response.strip()
        except Exception as e:
            return f"Error generating response from Hugging Face: {str(e)}"
