"""LangGraph agent: a small hand-built graph with a tool-calling LLM node
and a ToolNode, looping until the model stops requesting tools.
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.config import settings
from app.services.llm import LLMService, as_text
from app.services.tools import ToolService, build_tools
from app.utils.logger import logger
from app.utils.prompts import build_chat_prompt

SYSTEM_PROMPT = (
    "You are an intelligent AI assistant with access to tools. Use tools when "
    "they would improve the accuracy of your answer, then give a clear, direct "
    "final answer. Use at most 4 tool calls."
)

MAX_ITERATIONS = 4


class AgentState(TypedDict):
    messages: Annotated[list[Any], add_messages]


class AgentService:
    def __init__(self, llm_service: LLMService, tool_service: ToolService):
        self.llm_service = llm_service
        self.tool_service = tool_service
        # In-memory checkpointer: agent scratchpad persists per conversation_id
        # for the life of the process. A Postgres checkpointer would carry this
        # across restarts, but Message/Conversation tables remain the source
        # of truth for chat history either way.
        self._checkpointer = MemorySaver()

    def _build_graph(self, tools: list[Any]) -> Runnable:
        model = ChatGroq(
            model=settings.MODEL,
            api_key=SecretStr(settings.GROQ_API_KEY),
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_RESPONSE_TOKENS,
        ).bind_tools(tools)

        def call_model(state: AgentState) -> dict[str, Any]:
            response = model.invoke(state["messages"])
            return {"messages": [response]}

        graph = StateGraph(AgentState)
        graph.add_node("agent", call_model)
        graph.add_node("tools", ToolNode(tools))
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        return graph.compile(checkpointer=self._checkpointer)

    async def run(self, question: str, conversation_id: str, db: Session) -> dict[str, Any]:
        tools = build_tools(
            tool_service=self.tool_service,
            llm_service=self.llm_service,
            db=db,
            conversation_id=conversation_id,
        )
        graph = self._build_graph(tools)
        config: RunnableConfig = {
            "configurable": {"thread_id": conversation_id},
            "recursion_limit": MAX_ITERATIONS * 2 + 1,
        }
        try:
            result = await graph.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=question),
                    ]
                },
                config=config,
            )
        except Exception as e:
            # Groq's tool-calling occasionally emits malformed function-call
            # syntax the API itself rejects (tool_use_failed). Degrade to a
            # direct RAG-augmented answer — bypasses the flaky tool-calling
            # protocol but still grounds the response in retrieved documents
            # instead of surfacing a 500.
            logger.warning(f"Agent tool call failed for conv {conversation_id}, falling back: {e}")
            context = self.tool_service.rag_service.retrieve(question, k=3)
            prompt = build_chat_prompt(message=question, history=[], context=context)
            answer = await self.llm_service.generate(prompt)
            return {"answer": answer, "thoughts": [answer], "tool_calls": [], "usage": {}}

        messages = result["messages"]
        final = messages[-1]
        answer = as_text(final.content)

        thoughts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        prompt_tokens = 0
        completion_tokens = 0
        for m in messages:
            if isinstance(m, AIMessage):
                if m.content:
                    thoughts.append(as_text(m.content))
                for tc in m.tool_calls or []:
                    tool_calls.append({"tool": tc["name"], "input": tc["args"]})
                usage = getattr(m, "usage_metadata", None) or {}
                prompt_tokens += usage.get("input_tokens", 0)
                completion_tokens += usage.get("output_tokens", 0)

        logger.info(f"Agent completed for conv {conversation_id} with {len(tool_calls)} tool calls")
        return {
            "answer": answer,
            "thoughts": thoughts,
            "tool_calls": tool_calls,
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        }
