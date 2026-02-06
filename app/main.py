from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.api import chat, documents, health
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data/documents", exist_ok=True)
    os.makedirs("data/vectorstore", exist_ok=True)
    init_db()
    yield

app = FastAPI(
    title="AI Assistant Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
