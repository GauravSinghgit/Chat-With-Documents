from sqlalchemy.orm import Session
from app.config import settings
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.utils.logger import logger
from typing import List, Dict, Any


class ToolService:
    def __init__(self, rag_service: RAGService, memory_service: MemoryService):
        self.allowed_tools = settings.allowed_tools_list
        self.rag_service = rag_service
        self.memory_service = memory_service

    def execute_safe_tools(
        self,
        query: str,
        conversation_id: str,
        db: Session,
    ) -> List[Dict[str, Any]]:
        results = []

        if "search_documents" in self.allowed_tools:
            docs = self.rag_service.retrieve(query, k=3)
            if docs:
                results.append({"tool": "search_documents", "result": docs})
                logger.debug(f"search_documents returned {len(docs)} results")

        if "get_conversation_history" in self.allowed_tools:
            history = self.memory_service.get_history(db, conversation_id, limit=5)
            if history:
                results.append({"tool": "get_conversation_history", "result": history})

        if "search_web" in self.allowed_tools:
            web = self.search_web(query)
            if web:
                results.append({"tool": "search_web", "result": web})

        return results

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """DuckDuckGo web search — free, no API key needed."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            results = [
                {"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
                for r in raw
            ]
            logger.debug(f"Web search for '{query}' → {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return []
