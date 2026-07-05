import ast
import operator
from typing import Any, Dict, List

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.config import settings
from app.services.llm import LLMService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.utils.logger import logger


class ToolService:
    """Direct (non-agentic) tool access used by the plain RAG+tools chat path."""

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


# ─── LangGraph agent tools ─────────────────────────────────────────────────────

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST):
    """Evaluate a restricted arithmetic AST — no names, calls, or attribute access."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def build_tools(
    tool_service: ToolService,
    llm_service: LLMService,
    db: Session,
    conversation_id: str,
) -> List[Any]:
    """Build the LangChain tool list bound to this request's services/context,
    for use by the LangGraph agent (app/services/agent.py)."""

    @tool
    def search_documents(query: str) -> str:
        """Search the user's uploaded documents for passages relevant to the query."""
        results = tool_service.rag_service.retrieve(query, k=3)
        if not results:
            return "No relevant documents found."
        return "\n\n".join(r["content"] for r in results)

    @tool
    def search_web(query: str) -> str:
        """Search the public web for up-to-date information not in the documents."""
        results = tool_service.search_web(query, max_results=5)
        if not results:
            return "No web results found."
        return "\n\n".join(f"{r['title']}: {r['snippet']} ({r['url']})" for r in results)

    @tool
    def get_conversation_history(limit: int = 5) -> str:
        """Retrieve recent messages from this conversation for additional context."""
        history = tool_service.memory_service.get_history(db, conversation_id, limit=limit)
        if not history:
            return "No prior history."
        return "\n".join(f"{h['role']}: {h['content']}" for h in history)

    @tool
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4) / 5'."""
        try:
            return str(_safe_eval(ast.parse(expression, mode="eval").body))
        except Exception:
            return "Invalid expression."

    @tool
    def summarize_document(doc_id: int) -> str:
        """Return a short summary of a previously uploaded document, by its id."""
        from app.models import Document

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return f"Document {doc_id} not found."
        return doc.summary or (doc.content or "")[:500]

    @tool
    async def extract_structured_data(text: str, fields: str) -> str:
        """Extract the requested comma-separated fields from text and return
        them as compact JSON, e.g. fields='name, date, amount'."""
        prompt = (
            "Extract the following fields from the text below and return ONLY "
            f"compact JSON with exactly these keys: {fields}.\n\nText:\n{text}"
        )
        return await llm_service.generate(prompt)

    return [
        search_documents,
        search_web,
        get_conversation_history,
        calculator,
        summarize_document,
        extract_structured_data,
    ]
