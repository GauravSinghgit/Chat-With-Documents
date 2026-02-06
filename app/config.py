from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    HF_MODEL: str
    HF_BASE_URL: str
    HF_API_KEY: str
    # HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DATABASE_URL: str = "sqlite:///./data/conversations.db"
    VECTOR_STORE_PATH: str = "./data/vectorstore"
    DOCUMENTS_PATH: str = "./data/documents"
    MAX_CONTEXT_LENGTH: int = 4096
    MAX_RESPONSE_TOKENS: int = 512
    TEMPERATURE: float = 0.7
    TOP_K: int = 5
    ALLOWED_TOOLS: str = "search_documents,get_conversation_history"
    PII_MASKING_ENABLED: bool = True
    
    @property
    def allowed_tools_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_TOOLS.split(",")]
    
    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()