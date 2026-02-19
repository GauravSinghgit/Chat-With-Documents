# AI Assistant Platform v2.0

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
| **Rate limiting** | 30 req/min on chat, 10 req/min on uploads |
| **Dark mode** | Full light/dark theme toggle |
| **PII masking** | Auto-mask emails, phones, SSNs |

---

## Quick Start (Local)

### 1. Backend

```bash
cd AI-ASSISTANT-PLATFORM

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set GROQ_API_KEY=your_key_here

# IMPORTANT: Delete old DB if upgrading from v1
rm -rf data/

uvicorn app.main:app --reload --port 8000
```

- Backend: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

cp .env.local.example .env.local
# Already points to http://localhost:8000

npm install
npm run dev
```

- Frontend: http://localhost:3000

---

## Docker (Full Stack)

```bash
cp .env.example .env      # fill in GROQ_API_KEY

docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## Deploy: Render (Backend) + Vercel (Frontend)

### Backend → Render

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect repo — `render.yaml` is auto-detected
4. In Render dashboard → Environment:
   - Set `GROQ_API_KEY` = your key from [console.groq.com](https://console.groq.com)
5. Deploy (~3 min)

Backend URL: `https://ai-assistant-backend.onrender.com`

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import repo, set **Root Directory** = `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render URL
4. Deploy

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Get JWT token |
| GET | `/api/auth/me` | Required | Current user |
| POST | `/api/chat` | Optional | Standard chat (full response) |
| POST | `/api/chat/stream` | Optional | Streaming chat (SSE) |
| GET | `/api/conversations` | Required | List user conversations |
| GET | `/api/conversations/{id}/messages` | Required | Get messages |
| PATCH | `/api/conversations/{id}/title` | Required | Rename conversation |
| DELETE | `/api/conversations/{id}` | Required | Delete conversation |
| POST | `/api/documents/ingest` | Optional | Upload files (multi-file) |
| GET | `/api/documents` | Optional | List documents |
| GET | `/api/documents/{id}` | Optional | Get document details |
| DELETE | `/api/documents/{id}` | Required | Delete doc + vectors |
| POST | `/api/documents/{id}/reindex` | Required | Re-embed document |
| GET | `/api/health` | — | Health + stats |

---

## Environment Variables (.env)

```env
# Required
GROQ_API_KEY=your_groq_api_key

# JWT (change in production!)
JWT_SECRET=super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# LLM
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_RESPONSE_TOKENS=1024

# Features
PII_MASKING_ENABLED=true
ALLOWED_TOOLS=search_documents,get_conversation_history,search_web
TOP_K=5
```
 Run Locally — Two Terminals                                                   
                                                                                  Terminal 1 — Backend                                                                                                                                          
  cd D:\Dev\personal\AI-ASSISTANT-PLATFORM

  # Activate your Python 3.10 environment (already installed)
  venv\Scripts\activate   # if you have a venv, otherwise skip

  # Delete old DB (schema changed — one-time only)
  rmdir /s /q data

  # Start backend
  C:\Users\rudra\AppData\Local\Programs\Python\Python310\Scripts\uvicorn.exe    
  app.main:app --host 0.0.0.0 --port 8000 --reload

  Backend: http://localhost:8000/docs (Swagger UI)

  Terminal 2 — Frontend

  cd D:\Dev\personal\AI-ASSISTANT-PLATFORM\frontend

  # Already done: npm install ✓

  npm run dev

  Frontend: http://localhost:3000

  ---
  What was built

  Backend (all new on top of existing RAG):
  - POST /api/auth/register + POST /api/auth/login — JWT auth
  - POST /api/chat/stream — SSE streaming (token by token)
  - GET/DELETE /api/conversations — list + delete per user
  - POST /api/documents/ingest — multi-file upload (PDF/TXT/MD), auto-summary,  
  status tracking
  - GET/DELETE /api/documents/{id} + re-index endpoint
  - DuckDuckGo web search tool (free, no API key)
  - ReAct agent loop (use_agent: true in chat request)
  - Rate limiting (30/min chat, 10/min uploads)
  - Loguru structured logging → data/logs/app.log

  Frontend (frontend/):
  - Login + Register pages (JWT)
  - Chat sidebar with conversation history
  - Streaming chat interface (RAG / Web / Agent toggles)
  - Documents page — drag & drop upload, summary display, delete, re-index      
  - Dark/light mode toggle

  Deployment:
  - Dockerfile + docker-compose.yml for local Docker
  - render.yaml for one-click Render deploy