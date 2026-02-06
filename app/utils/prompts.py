from typing import List, Dict, Any

def build_chat_prompt(
    message: str,
    history: List[Dict[str, str]],
    context: List[Dict[str, Any]] = None,
    tool_results: List[Dict[str, Any]] = None
) -> str:
    prompt_parts = ["<s>[INST] You are a helpful AI assistant."]
    
    if context:
        prompt_parts.append("\nRelevant context:")
        for ctx in context[:3]:
            prompt_parts.append(f"- {ctx['content'][:300]}")
    
    if tool_results:
        prompt_parts.append("\nTool results:")
        for tool in tool_results:
            prompt_parts.append(f"- {tool['tool']}: {str(tool['result'])[:200]}")
    
    if history:
        prompt_parts.append("\nConversation history:")
        for msg in history[-5:]:
            prompt_parts.append(f"{msg['role']}: {msg['content'][:200]}")
    
    prompt_parts.append(f"\nUser: {message}")
    prompt_parts.append("\nAssistant: [/INST]")
    
    return "\n".join(prompt_parts)