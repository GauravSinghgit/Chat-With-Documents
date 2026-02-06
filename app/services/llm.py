from huggingface_hub import InferenceClient
from app.config import settings


class LLMService:
    def __init__(self):
        """
        Initialize the Hugging Face inference client.

        We explicitly pass the base URL so that we use the new
        `https://router.huggingface.co` endpoint instead of the
        deprecated `https://api-inference.huggingface.co`.
        Make sure `HF_BASE_URL` in your `.env` is set to:
            HF_BASE_URL=https://router.huggingface.co
        """
        self.client = InferenceClient(
            model=settings.HF_MODEL,
            token=settings.HF_API_KEY,
            base_url=settings.HF_BASE_URL,
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
            # Keep the existing behavior of returning an error string so the
            # API response shape does not change, but make the message clearer.
            return f"Error generating response from Hugging Face: {str(e)}"