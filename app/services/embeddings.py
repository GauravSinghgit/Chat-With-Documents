from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


class EmbeddingService:
    """Wraps the configured sentence-transformers model behind LangChain's
    Embeddings interface so it plugs directly into the PGVector store."""

    def __init__(self):
        self.model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
