# AI Assistant Platform v2.0

[![Backend CI](https://github.com/GauravSinghgit/AI-ASSISTANT-PLATFORM/actions/workflows/backend.yml/badge.svg)](https://github.com/GauravSinghgit/AI-ASSISTANT-PLATFORM/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/GauravSinghgit/AI-ASSISTANT-PLATFORM/actions/workflows/frontend.yml/badge.svg)](https://github.com/GauravSinghgit/AI-ASSISTANT-PLATFORM/actions/workflows/frontend.yml)

A production-ready AI assistant with RAG, streaming chat, JWT auth, agentic tools, and a full Next.js + shadcn/ui frontend.

---

## Features

| Feature | Description |
|---|---|
| **Streaming chat** | Token-by-token response via SSE |
| **RAG** | FAISS vector search over uploaded documents |
| **JWT Auth** | Register/login with Bearer tokens (7-day expiry) |
| **Agentic loop** | ReAct agent with multi-step tool use |
| **Web search** | DuckDuckGo — free, no API key needed |
| **Document management** | Upload PDF/TXT/MD, auto-summary, delete, re-index |
| **Document → Chat** | "Chat" button on every document opens a focused chat |
| **Rate limiting** | 30 req/min on chat, 10 req/min on uploads |
| **Dark mode** | Full light/dark theme toggle |
| **PII masking** | Auto-mask emails, phones, SSNs |

---

## Tech Stack

| Layer | Tech |
|---|---|
| LLM | [Groq](https://console.groq.com) — `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector Store | FAISS (cosine similarity) |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | Next.js 14 App Router + shadcn/ui + Tailwind |

---

## Quick Start (Local)

### 1. Backend

```bash
git clone <repo-url>
cd AI-ASSISTANT-PLATFORM

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Set GROQ_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:3000

---

## Environment Variables (`.env`)

```env
# Required
GROQ_API_KEY=your_groq_api_key

# LLM — use an active Groq model (llama3-8b-8192 is decommissioned)
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_RESPONSE_TOKENS=1024
MAX_CONTEXT_LENGTH=4096

# Tools
ALLOWED_TOOLS=search_documents,get_conversation_history,search_web
TOP_K=5

# JWT (change in production!)
JWT_SECRET=change-this-to-a-very-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Security
PII_MASKING_ENABLED=true
```

> **Important:** `llama3-8b-8192` has been decommissioned by Groq. Use `llama-3.3-70b-versatile` or check [Groq's model list](https://console.groq.com/docs/models).

---

## Docker

```bash
cp .env.example .env   # set GROQ_API_KEY
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## Deploy: Render + Vercel

### Backend → Render
1. Push to GitHub
2. Render → New Web Service → connect repo (`render.yaml` auto-detected)
3. Set env var: `GROQ_API_KEY`

### Frontend → Vercel
1. Vercel → New Project → import repo
2. Set **Root Directory** = `frontend`
3. Set env var: `NEXT_PUBLIC_API_URL` = your Render backend URL

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Get JWT token |
| GET | `/api/auth/me` | Required | Current user |
| POST | `/api/chat` | Optional | Standard chat |
| POST | `/api/chat/stream` | Optional | Streaming chat (SSE) |
| GET | `/api/conversations` | Required | List conversations |
| GET | `/api/conversations/{id}/messages` | Required | Get messages |
| PATCH | `/api/conversations/{id}/title` | Required | Rename |
| DELETE | `/api/conversations/{id}` | Required | Delete |
| POST | `/api/documents/ingest` | Optional | Upload PDF/TXT/MD |
| GET | `/api/documents` | Optional | List documents |
| GET | `/api/documents/{id}` | Optional | Get document |
| DELETE | `/api/documents/{id}` | Required | Delete + remove vectors |
| POST | `/api/documents/{id}/reindex` | Required | Re-embed document |
| GET | `/api/health` | — | Health + stats |

---

## Project Structure

```
AI-ASSISTANT-PLATFORM/
├── app/
│   ├── api/            # routes: auth, chat, documents, conversations, health
│   ├── services/       # llm, embeddings, vectorstore, rag, agent, tools, memory
│   ├── utils/          # logger, rate_limit, security, prompts
│   ├── config.py       # Pydantic settings from .env
│   ├── models.py       # SQLAlchemy ORM (User, Conversation, Message, Document)
│   ├── schemas.py      # Pydantic request/response models
│   └── main.py         # FastAPI app entry point
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # /login, /register
│   │   ├── chat/            # /chat + /chat/[id] — with sidebar layout
│   │   └── documents/       # /documents — with sidebar layout
│   ├── components/
│   │   ├── chat/            # ChatSidebar, ChatInterface, ChatInput, MessageBubble
│   │   └── ui/              # shadcn/ui components
│   └── lib/
│       ├── api/             # fetch clients: auth, chat, documents
│       └── hooks/           # useStreamChat, useAuth
├── data/                    # runtime data (gitignored)
│   ├── conversations.db     # SQLite
│   ├── vectorstore/         # FAISS index + metadata.pkl
│   └── logs/
├── docker-compose.yml
├── Dockerfile
├── render.yaml
└── requirements.txt
```

---

## Bugs Fixed

| Bug | Root Cause | Fix |
|---|---|---|
| Upload hangs forever | `generate()` called sync Groq client inside `async def`, blocking the event loop | Switched to `await async_client.chat.completions.create(...)` |
| 400 on all LLM calls | `llama3-8b-8192` decommissioned by Groq | Updated model to `llama-3.3-70b-versatile` |
| Raw errors shown in UI | `str(e)` returned directly in SSE stream and API responses | All errors return generic messages; raw details only in server logs |
| Documents not visible after upload | `chunk_count`/`page_count` can be `None`, causing Pydantic 500 on list endpoint | Added `= 0` defaults to schema fields |
| Documents page had no sidebar | Standalone page outside chat layout | Added `documents/layout.tsx` with shared `ChatSidebar` |
| `fetchDocs` silent failure | No error shown when list API fails | Added `toast.error` on failure |
