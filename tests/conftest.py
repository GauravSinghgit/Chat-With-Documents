import os
from collections.abc import AsyncGenerator
from typing import Any

# Must be set before anything under app/ is imported — Settings() has no
# defaults for these on purpose (see app/config.py).
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DEBUG", "true")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import (
    get_agent_service,
    get_embedding_service,
    get_llm_service,
    get_vectorstore_service,
)
from app.main import app

# ─── Fakes: no real Postgres/pgvector/Groq calls in tests ─────────────────────


class FakeEmbeddingService:
    model = None


class FakeVectorStoreService:
    """In-memory stand-in for the PGVector-backed VectorStoreService."""

    def __init__(self):
        self._chunks: list[dict[str, Any]] = []

    def add_documents(self, texts: list[str], metadatas: list[dict[str, Any]]) -> None:
        for text, meta in zip(texts, metadatas, strict=False):
            self._chunks.append({"content": text, "metadata": meta})

    def delete_by_doc_id(self, doc_id: int) -> None:
        self._chunks = [c for c in self._chunks if c["metadata"].get("doc_id") != doc_id]

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        return [{**c, "score": 0.9} for c in self._chunks[:k]]

    def get_stats(self) -> dict[str, Any]:
        return {"collection": "test", "index_type": "fake", "total": len(self._chunks)}


class FakeLLMService:
    async def generate(self, prompt: str) -> str:
        return "fake llm answer"

    async def generate_with_usage(self, prompt: str):
        return "fake llm answer", {"prompt_tokens": 10, "completion_tokens": 5}

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        for token in ["Hello", " world"]:
            yield token


class FakeAgentService:
    async def run(self, question: str, conversation_id: str, db) -> dict[str, Any]:
        return {
            "answer": "fake agent answer",
            "thoughts": ["fake agent answer"],
            "tool_calls": [],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4},
        }


# ─── DB: shared in-memory SQLite for the lifetime of the test session ─────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    import app.models  # noqa: F401 — register models on Base before create_all

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _override_dependencies():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_embedding_service] = lambda: FakeEmbeddingService()
    app.dependency_overrides[get_vectorstore_service] = lambda: FakeVectorStoreService()
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    app.dependency_overrides[get_agent_service] = lambda: FakeAgentService()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clean_tables():
    """Each test starts with empty tables (fast — in-memory SQLite)."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client():
    """A TestClient that has already registered + logged in a user — the
    httpOnly cookie set by /api/auth/login persists across requests made
    with this same client instance. Deliberately a *separate* TestClient
    instance from `client` (not built on top of it) so a test can request
    both an authenticated and a genuinely anonymous client at once."""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        c.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "TestPass123!",
                "full_name": "Test User",
            },
        )
        c.post(
            "/api/auth/login",
            data={"username": "user@example.com", "password": "TestPass123!"},
        )
        yield c


@pytest.fixture
def admin_client():
    """A TestClient logged in as an is_admin=True user (separate instance —
    see auth_client's docstring)."""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        c.post(
            "/api/auth/register",
            json={"email": "admin@example.com", "password": "TestPass123!", "full_name": "Admin"},
        )
        db = TestingSessionLocal()
        try:
            from app.models import User

            user = db.query(User).filter(User.email == "admin@example.com").first()
            user.is_admin = True
            db.commit()
        finally:
            db.close()
        c.post(
            "/api/auth/login",
            data={"username": "admin@example.com", "password": "TestPass123!"},
        )
        yield c
