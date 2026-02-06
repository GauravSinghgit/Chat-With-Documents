from sqlalchemy.orm import Session
from app.config import settings
from app.services.memory import MemoryService
from app.services.rag import RAGService
from typing import List, Dict, Any


class ToolService:
    def __init__(
        self,
        rag_service: RAGService,
        memory_service: MemoryService,
    ):
        self.allowed_tools = settings.allowed_tools_list
        self.rag_service = rag_service
        self.memory_service = memory_service

    def execute_safe_tools(
        self,
        query: str,
        conversation_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        results = []

        if "search_documents" in self.allowed_tools:
            docs = self.rag_service.retrieve(query, k=3)
            if docs:
                results.append({
                    "tool": "search_documents",
                    "result": docs
                })

        if "get_conversation_history" in self.allowed_tools:
            history = self.memory_service.get_history(db, conversation_id, limit=5)
            if history:
                results.append({
                    "tool": "get_conversation_history",
                    "result": history
                })

        return results
