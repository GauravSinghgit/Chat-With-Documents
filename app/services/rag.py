from typing import Any

from app.config import settings
from app.services.vectorstore import VectorStoreService


class RAGService:
    def __init__(self, vectorstore_service: VectorStoreService):
        self.vectorstore = vectorstore_service

    def retrieve(self, query: str, k: int | None = None) -> list[dict[str, Any]]:
        if k is None:
            k = settings.TOP_K
        return self.vectorstore.search(query, k=k)
