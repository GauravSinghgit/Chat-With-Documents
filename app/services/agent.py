"""
ReAct Agent — Think → Act → Observe loop.
The LLM decides which tools to call and iterates until it has a final answer.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.llm import LLMService
from app.services.tools import ToolService
from app.utils.logger import logger

REACT_SYSTEM_PROMPT = """You are an intelligent AI assistant with access to tools.
Reason step-by-step and use tools when needed to give accurate answers.

Available tools:
- search_documents: Search uploaded knowledge base documents
- get_conversation_history: Retrieve past conversation context
- search_web: Search the web for up-to-date information

Format your response EXACTLY like this:
THOUGHT: [your reasoning about what to do]
ACTION: [tool_name or NONE]
INPUT: [input for the tool, or leave blank if ACTION is NONE]

After receiving tool results, continue reasoning until you have enough info, then:
FINAL ANSWER: [your complete, helpful answer to the user]

Rules:
- Always start with THOUGHT
- Use FINAL ANSWER when you have enough information
- Keep tool inputs concise and specific
- Maximum 4 tool calls per query
"""


class AgentService:
    def __init__(self, llm_service: LLMService, tool_service: ToolService):
        self.llm = llm_service
        self.tool_service = tool_service
        self.max_iterations = 4

    async def run(
        self,
        question: str,
        conversation_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        prompt = f"{REACT_SYSTEM_PROMPT}\n\nUser question: {question}\n\n"
        thoughts: List[str] = []
        tool_calls: List[Dict] = []

        for iteration in range(self.max_iterations):
            logger.debug(f"Agent iteration {iteration + 1}")
            response = await self.llm.generate(prompt)
            thoughts.append(response)

            # Found final answer
            if "FINAL ANSWER:" in response:
                answer = response.split("FINAL ANSWER:")[-1].strip()
                logger.info(f"Agent completed in {iteration + 1} iterations")
                return {
                    "answer": answer,
                    "thoughts": thoughts,
                    "tool_calls": tool_calls,
                }

            # Parse ACTION and INPUT
            action, tool_input = self._parse_action(response)

            if action and action.upper() != "NONE":
                result = self._execute_tool(action, tool_input, conversation_id, db)
                tool_calls.append({"tool": action, "input": tool_input, "result": result})
                logger.info(f"Agent called tool: {action}")
                # Append observation to prompt for next iteration
                observation = str(result)[:800]
                prompt += f"{response}\nOBSERVATION from {action}: {observation}\n\n"
            else:
                # No action — treat as final answer
                break

        # Fallback: return last thought as answer
        final = thoughts[-1] if thoughts else "I could not generate a response."
        if "FINAL ANSWER:" in final:
            final = final.split("FINAL ANSWER:")[-1].strip()
        return {"answer": final, "thoughts": thoughts, "tool_calls": tool_calls}

    def _parse_action(self, response: str):
        action = None
        tool_input = ""
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("INPUT:"):
                tool_input = line.replace("INPUT:", "").strip()
        return action, tool_input

    def _execute_tool(self, tool_name: str, query: str, conversation_id: str, db: Session):
        tool_name = tool_name.lower().strip()
        try:
            if tool_name == "search_documents":
                return self.tool_service.rag_service.retrieve(query)
            elif tool_name == "get_conversation_history":
                return self.tool_service.memory_service.get_history(db, conversation_id, limit=5)
            elif tool_name == "search_web":
                return self.tool_service.search_web(query)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return "Tool execution failed. Continuing without this result."
