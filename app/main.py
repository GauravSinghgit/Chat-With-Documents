import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.database import init_db
from app.api import chat, documents, health
from app.api import auth, conversations
from app.utils.rate_limit import limiter
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create required directories
    os.makedirs("data/documents", exist_ok=True)
    os.makedirs("data/vectorstore", exist_ok=True)
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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your frontend URL in production
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


# ─── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )
