import json
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas import ChatRequest, ChatResponse
from app.database import get_db
from app.models import Conversation, User
from app.dependencies import (
    get_llm_service,
    get_memory_service,
    get_rag_service,
    get_tool_service,
    get_agent_service,
    get_current_user_optional,
)
from app.services.llm import LLMService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.tools import ToolService
from app.services.agent import AgentService
from app.utils.security import sanitize_input, mask_pii
from app.utils.prompts import build_chat_prompt
from app.utils.rate_limit import limiter
from app.utils.logger import logger

router = APIRouter(tags=["chat"])


def _link_conversation_to_user(db: Session, conversation_id: str, user: Optional[User]):
    if user:
        conv = db.query(Conversation).filter_by(id=conversation_id).first()
        if conv and conv.user_id is None:
            conv.user_id = user.id
            db.commit()


# ─── Standard Chat ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat(
    request: Request,           # FastAPI Request — required by slowapi
    body: ChatRequest,          # actual JSON payload
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
    rag_service: RAGService = Depends(get_rag_service),
    tool_service: ToolService = Depends(get_tool_service),
    agent_service: AgentService = Depends(get_agent_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    sanitized = sanitize_input(body.message)
    masked = mask_pii(sanitized)

    memory_service.ensure_conversation(db, body.conversation_id)
    _link_conversation_to_user(db, body.conversation_id, current_user)
    memory_service.add_message(db, body.conversation_id, "user", sanitized)

    history = memory_service.get_history(db, body.conversation_id, limit=10)

    # ── Agentic loop ──────────────────────────────────────────────────────────
    if body.use_agent:
        result = await agent_service.run(masked, body.conversation_id, db)
        response_text = result["answer"]
        memory_service.add_message(db, body.conversation_id, "assistant", response_text)
        logger.info(f"Agent response for conv {body.conversation_id}")
        return ChatResponse(
            conversation_id=body.conversation_id,
            message=response_text,
            tool_calls=[tc["tool"] for tc in result["tool_calls"]],
            agent_thoughts=result["thoughts"],
        )

    # ── Standard RAG + Tools ──────────────────────────────────────────────────
    sources = rag_service.retrieve(masked) if body.use_rag else []
    tool_results = (
        tool_service.execute_safe_tools(masked, body.conversation_id, db)
        if body.use_tools else []
    )

    prompt = build_chat_prompt(
        message=masked,
        history=history,
        context=sources,
        tool_results=tool_results,
    )

    response_text = await llm_service.generate(prompt)
    memory_service.add_message(db, body.conversation_id, "assistant", response_text)
    _maybe_set_title(db, body.conversation_id, sanitized)

    logger.info(f"Chat response for conv {body.conversation_id} (rag={body.use_rag})")
    return ChatResponse(
        conversation_id=body.conversation_id,
        message=response_text,
        sources=[{"content": s["content"][:200], "score": s["score"]} for s in sources],
        tool_calls=[t["tool"] for t in tool_results],
    )


# ─── Streaming Chat ─────────────────────────────────────────────────────────────

@router.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,           # required by slowapi
    body: ChatRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
    rag_service: RAGService = Depends(get_rag_service),
    tool_service: ToolService = Depends(get_tool_service),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    sanitized = sanitize_input(body.message)
    masked = mask_pii(sanitized)

    memory_service.ensure_conversation(db, body.conversation_id)
    _link_conversation_to_user(db, body.conversation_id, current_user)
    memory_service.add_message(db, body.conversation_id, "user", sanitized)

    history = memory_service.get_history(db, body.conversation_id, limit=10)
    sources = rag_service.retrieve(masked) if body.use_rag else []
    tool_results = (
        tool_service.execute_safe_tools(masked, body.conversation_id, db)
        if body.use_tools else []
    )

    prompt = build_chat_prompt(
        message=masked,
        history=history,
        context=sources,
        tool_results=tool_results,
    )

    sources_payload = [{"content": s["content"][:200], "score": s["score"]} for s in sources]

    async def event_generator():
        full_response = ""
        try:
            async for token in llm_service.generate_stream(prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        memory_service.add_message(db, body.conversation_id, "assistant", full_response)
        _maybe_set_title(db, body.conversation_id, sanitized)

        done = {
            "type": "done",
            "conversation_id": body.conversation_id,
            "sources": sources_payload,
            "tool_calls": [t["tool"] for t in tool_results],
        }
        yield f"data: {json.dumps(done)}\n\n"
        logger.info(f"Stream complete for conv {body.conversation_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _maybe_set_title(db: Session, conversation_id: str, first_message: str):
    conv = db.query(Conversation).filter_by(id=conversation_id).first()
    if conv and (conv.title is None or conv.title == "New Conversation"):
        title = first_message[:60].strip()
        if len(first_message) > 60:
            title += "…"
        conv.title = title
        db.commit()
