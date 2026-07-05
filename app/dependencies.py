from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.models import User
from app.services.llm import LLMService
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.tools import ToolService
from app.services.agent import AgentService
from app.utils.auth_utils import decode_access_token

security = HTTPBearer(auto_error=False)


# ─── Settings ────────────────────────────────────────────────────────────────

@lru_cache()
def get_settings():
    return Settings()


# ─── Services (singletons via lru_cache) ─────────────────────────────────────

@lru_cache()
def get_llm_service():
    return LLMService()


@lru_cache()
def get_embedding_service():
    return EmbeddingService()


@lru_cache()
def get_vectorstore_service():
    return VectorStoreService(embedding_service=get_embedding_service())


def get_memory_service():
    return MemoryService()


def get_rag_service(
    vectorstore_service: VectorStoreService = Depends(get_vectorstore_service),
):
    return RAGService(vectorstore_service=vectorstore_service)


def get_tool_service(
    rag_service: RAGService = Depends(get_rag_service),
    memory_service: MemoryService = Depends(get_memory_service),
):
    return ToolService(
        rag_service=rag_service,
        memory_service=memory_service,
    )


def get_agent_service(
    llm_service: LLMService = Depends(get_llm_service),
    tool_service: ToolService = Depends(get_tool_service),
):
    return AgentService(llm_service=llm_service, tool_service=tool_service)


# ─── Auth Dependencies ────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Returns None if no/invalid token — used for optional auth endpoints."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    return db.query(User).filter(User.id == payload.get("sub")).first()
