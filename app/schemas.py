import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# ─── Auth ────────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    is_admin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ─── Conversation ─────────────────────────────────────────────────────────────


class ConversationResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int | None = 0

    model_config = ConfigDict(from_attributes=True)


# ─── Message ─────────────────────────────────────────────────────────────────


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Chat ─────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    use_rag: bool = True
    use_tools: bool = True
    use_agent: bool = False  # Enable ReAct agentic loop


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    sources: list[dict[str, Any]] | None = None
    tool_calls: list[str] | None = None
    agent_thoughts: list[str] | None = None


# ─── Document ─────────────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str | None = None
    file_type: str | None = None
    file_size: int = 0
    chunk_count: int = 0
    page_count: int = 0
    status: str
    summary: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def fill_nullable_fields(self) -> "DocumentResponse":
        """Back-fill original_filename and file_type from filename for legacy rows."""
        if not self.original_filename:
            self.original_filename = self.filename or ""
        if not self.file_type:
            ext = os.path.splitext(self.original_filename or self.filename or "")[-1]
            self.file_type = ext.lstrip(".") if ext else "unknown"
        return self

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentResponse]


# ─── Admin / Usage Analytics ──────────────────────────────────────────────────


class UsageTotals(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_latency_ms: float


class UsageByUser(BaseModel):
    user_id: str | None
    email: str | None
    requests: int
    total_tokens: int


class UsageByDay(BaseModel):
    date: str
    requests: int
    total_tokens: int


class AdminStatsResponse(BaseModel):
    totals: UsageTotals
    by_user: list[UsageByUser]
    by_day: list[UsageByDay]


# ─── Health ───────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str = "2.0.0"
    services: dict[str, str] | None = None
