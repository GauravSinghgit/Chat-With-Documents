import os
from fastapi import APIRouter, Depends
from app.schemas import HealthResponse
from app.dependencies import get_vectorstore_service
from app.services.vectorstore import VectorStoreService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(vectorstore: VectorStoreService = Depends(get_vectorstore_service)):
    stats = vectorstore.get_stats()
    return HealthResponse(
        status="ok",
        version="2.0.0",
        services={
            "llm": "groq",
            "embeddings": "sentence-transformers",
            "vectorstore": f"faiss ({stats['total_vectors']} vectors)",
            "database": "sqlite",
        },
    )
