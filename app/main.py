import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin, auth, chat, conversations, documents, health
from app.config import settings
from app.database import init_db
from app.utils.logger import logger
from app.utils.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # data/logs is the only local directory the app still writes to
    # (loguru's file sink) — documents and vectors live entirely in Postgres.
    os.makedirs("data/logs", exist_ok=True)
    # Initialize database tables
    init_db()
    logger.info("AI Assistant Platform v2.0 started")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Assistant Platform",
    description="Production-ready AI assistant with RAG, streaming, auth, and agentic tools.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Rate Limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# ─── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )
