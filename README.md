# LLM-Powered AI Assistant Platform

Production-ready FastAPI backend with RAG, memory, and tool calling.

## Features
- Hugging Face Inference API integration
- FAISS vector search
- SQLite conversation memory
- Document ingestion and retrieval
- PII masking and security guardrails
- Tool calling with safe templates

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your HF_API_KEY
uvicorn app.main:app --reload
```

## Endpoints
- POST /api/chat - Send message with memory and RAG
- POST /api/documents/ingest - Upload documents
- GET /api/health - Health check