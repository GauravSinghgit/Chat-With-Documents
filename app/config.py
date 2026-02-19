from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # LLM
    MODEL: str = "llama-3.3-70b-versatile"
    GROQ_API_KEY: str

    # Embeddings & Vector Store
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_STORE_PATH: str = "./data/vectorstore"

    # Database
    DATABASE_URL: str = "sqlite:///./data/conversations.db"
    DOCUMENTS_PATH: str = "./data/documents"

    # LLM Parameters
    MAX_CONTEXT_LENGTH: int = 4096
    MAX_RESPONSE_TOKENS: int = 1024
    TEMPERATURE: float = 0.7
    TOP_K: int = 5

    # Tools
    ALLOWED_TOOLS: str = "search_documents,get_conversation_history,search_web"

    # Security / PII
    PII_MASKING_ENABLED: bool = True

    # JWT Auth
    JWT_SECRET: str = "change-this-to-a-very-long-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Rate Limiting
    RATE_LIMIT_CHAT: str = "30/minute"
    RATE_LIMIT_DOCS: str = "10/minute"

    @property
    def allowed_tools_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_TOOLS.split(",")]

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()
