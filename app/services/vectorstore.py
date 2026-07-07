"""Postgres-backed vector store (pgvector via LangChain's PGVector)."""

from typing import Any

from langchain_postgres import PGVector

from app.config import settings
from app.services.embeddings import EmbeddingService
from app.utils.logger import logger

COLLECTION_NAME = "document_chunks"


class VectorStoreService:
    def __init__(self, embedding_service: EmbeddingService):
        self.store = PGVector(
            embeddings=embedding_service.model,
            collection_name=COLLECTION_NAME,
            connection=settings.DATABASE_URL,
            use_jsonb=True,
        )
        logger.info(f"Connected to pgvector collection '{COLLECTION_NAME}'")

    def add_documents(self, texts: list[str], metadatas: list[dict[str, Any]]) -> None:
        self.store.add_texts(texts, metadatas=metadatas)
        logger.debug(f"Added {len(texts)} chunks to pgvector")

    def delete_by_doc_id(self, doc_id: int) -> None:
        self.store.delete(filter={"doc_id": doc_id})
        logger.info(f"Deleted vectors for doc_id={doc_id}")

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        results = self.store.similarity_search_with_score(query, k=k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": float(score)}
            for doc, score in results
        ]

    def get_stats(self) -> dict[str, Any]:
        return {
            "collection": COLLECTION_NAME,
            "index_type": "pgvector (cosine similarity)",
        }
