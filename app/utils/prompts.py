from typing import List, Dict, Any


def build_chat_prompt(
    message: str,
    history: List[Dict[str, str]],
    context: List[Dict[str, Any]] = None,
    tool_results: List[Dict[str, Any]] = None,
) -> str:
    """
    Build a prompt string for Groq's chat API using llama-3.3-70b-versatile.
    Groq accepts plain OpenAI-style messages, so we construct a single
    user-turn string that packages system instructions + retrieved context
    + conversation history + the current question.
    """

    system_lines = [
        "You are a helpful, accurate AI assistant.",
        "Answer the user's question using the provided context and conversation history.",
        "If the context contains relevant information, use it and cite it clearly.",
        "If you don't know the answer, say so — do not make up facts.",
    ]

    # ── Retrieved document chunks ─────────────────────────────────────────────
    if context:
        system_lines.append("\n### Relevant Document Context")
        for i, ctx in enumerate(context, 1):
            content = ctx.get("content", "").strip()
            score = ctx.get("score", 0)
            system_lines.append(f"[Chunk {i} | relevance: {score:.2f}]\n{content}")

    # ── Tool results ──────────────────────────────────────────────────────────
    if tool_results:
        system_lines.append("\n### Tool Results")
        for t in tool_results:
            result_text = str(t.get("result", "")).strip()[:1000]
            system_lines.append(f"[{t['tool']}]\n{result_text}")

    # ── Conversation history ──────────────────────────────────────────────────
    history_block = ""
    if history:
        lines = []
        for msg in history[-10:]:
            role = msg["role"].capitalize()
            content = msg["content"].strip()
            lines.append(f"{role}: {content}")
        history_block = "\n### Conversation History\n" + "\n".join(lines)

    system_text = "\n".join(system_lines)

    prompt = (
        f"{system_text}"
        f"{history_block}"
        f"\n\n### Current Question\nUser: {message}\nAssistant:"
    )

    return prompt
