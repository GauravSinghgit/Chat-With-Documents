from typing import List, Dict, Any
from app.config import settings
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService


class RAGService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vectorstore_service: VectorStoreService,
    ):
        self.embedding_service = embedding_service
        self.vectorstore = vectorstore_service

    def retrieve(self, query: str, k: int | None = None) -> List[Dict[str, Any]]:
        if k is None:
            k = settings.TOP_K

        query_embedding = self.embedding_service.embed_query(query)
        results = self.vectorstore.search(query_embedding, k=k)
        return results
