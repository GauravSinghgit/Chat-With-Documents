from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    use_rag: bool = True
    use_tools: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    sources: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[str]] = None

class DocumentIngest(BaseModel):
    filename: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"