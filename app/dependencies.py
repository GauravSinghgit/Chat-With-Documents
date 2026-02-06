from functools import lru_cache
from fastapi import Depends

from app.config import Settings
from app.services.llm import LLMService
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.tools import ToolService


@lru_cache()
def get_settings():
    return Settings()


@lru_cache()
def get_llm_service():
    return LLMService()


@lru_cache()
def get_embedding_service():
    return EmbeddingService()


@lru_cache()
def get_vectorstore_service():
    return VectorStoreService()


def get_memory_service():
    return MemoryService()


def get_rag_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vectorstore_service: VectorStoreService = Depends(get_vectorstore_service),
):
    return RAGService(
        embedding_service=embedding_service,
        vectorstore_service=vectorstore_service,
    )


def get_tool_service(
    rag_service: RAGService = Depends(get_rag_service),
    memory_service: MemoryService = Depends(get_memory_service),
):
    return ToolService(
        rag_service=rag_service,
        memory_service=memory_service,
    )
