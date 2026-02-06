from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import ChatRequest, ChatResponse
from app.database import get_db
from app.dependencies import (
    get_llm_service,
    get_memory_service,
    get_rag_service,
    get_tool_service
)
from app.services.llm import LLMService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.tools import ToolService
from app.utils.security import sanitize_input, mask_pii
from app.utils.prompts import build_chat_prompt

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
    rag_service: RAGService = Depends(get_rag_service),
    tool_service: ToolService = Depends(get_tool_service)
):
    sanitized_message = sanitize_input(request.message)
    masked_message = mask_pii(sanitized_message)
    
    memory_service.ensure_conversation(db, request.conversation_id)
    memory_service.add_message(db, request.conversation_id, "user", sanitized_message)
    
    history = memory_service.get_history(db, request.conversation_id, limit=10)
    
    sources = []
    if request.use_rag:
        sources = rag_service.retrieve(masked_message)
    
    tool_results = []
    if request.use_tools:
        tool_results = tool_service.execute_safe_tools(
            masked_message,
            request.conversation_id,
            db
        )
    
    prompt = build_chat_prompt(
        message=masked_message,
        history=history,
        context=sources,
        tool_results=tool_results
    )
    
    response = await llm_service.generate(prompt)
    
    memory_service.add_message(db, request.conversation_id, "assistant", response)
    
    return ChatResponse(
        conversation_id=request.conversation_id,
        message=response,
        sources=[{"content": s["content"][:200], "score": s["score"]} for s in sources],
        tool_calls=[t["tool"] for t in tool_results]
    )