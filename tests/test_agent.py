"""Unit tests for the LangGraph agent (app/services/agent.py) — ChatGroq is
monkeypatched so these run with no network access and no Groq API key."""
import pytest
from langchain_core.messages import AIMessage

from app.services.agent import AgentService
from app.services.rag import RAGService
from app.services.tools import ToolService


class FakeChatModel:
    """Stands in for a ChatGroq instance: .bind_tools() returns self,
    .invoke() replays a scripted sequence of AIMessage responses."""

    def __init__(self, responses):
        self._responses = list(responses)

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return self._responses.pop(0)


class FakeVectorStore:
    def search(self, query, k=5):
        return []


class FakeMemoryService:
    def get_history(self, db, conversation_id, limit=5):
        return []


def _make_agent_service(responses, monkeypatch):
    monkeypatch.setattr(
        "app.services.agent.ChatGroq", lambda **kwargs: FakeChatModel(responses)
    )
    tool_service = ToolService(
        rag_service=RAGService(vectorstore_service=FakeVectorStore()),
        memory_service=FakeMemoryService(),
    )
    return AgentService(llm_service=None, tool_service=tool_service)


@pytest.mark.asyncio
async def test_agent_answers_directly_with_no_tool_calls(monkeypatch):
    responses = [AIMessage(content="Paris is the capital of France.", tool_calls=[])]
    agent = _make_agent_service(responses, monkeypatch)

    result = await agent.run("What is the capital of France?", "conv-1", db=None)

    assert result["answer"] == "Paris is the capital of France."
    assert result["tool_calls"] == []


@pytest.mark.asyncio
async def test_agent_calls_calculator_then_answers(monkeypatch):
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "calculator", "args": {"expression": "2 + 2"}, "id": "call_1"}],
        ),
        AIMessage(content="The answer is 4.", tool_calls=[]),
    ]
    agent = _make_agent_service(responses, monkeypatch)

    result = await agent.run("What is 2 + 2?", "conv-2", db=None)

    assert result["answer"] == "The answer is 4."
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "calculator"


class _RaisingChatModel:
    """Simulates Groq's tool_use_failed error, which surfaces when the
    compiled graph actually invokes the model — not at construction time."""

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        raise RuntimeError("simulated tool_use_failed from Groq")


@pytest.mark.asyncio
async def test_agent_falls_back_to_rag_answer_on_tool_call_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.agent.ChatGroq", lambda **kwargs: _RaisingChatModel()
    )

    class FakeLLM:
        async def generate(self, prompt):
            return "fallback answer"

    tool_service = ToolService(
        rag_service=RAGService(vectorstore_service=FakeVectorStore()),
        memory_service=FakeMemoryService(),
    )
    agent = AgentService(llm_service=FakeLLM(), tool_service=tool_service)

    result = await agent.run("This will error", "conv-3", db=None)

    assert result["answer"] == "fallback answer"
    assert result["tool_calls"] == []
