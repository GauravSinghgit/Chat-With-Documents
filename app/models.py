from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    full_name: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None)
    title: Mapped[str | None] = mapped_column(default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    user: Mapped["User | None"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str]  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None)
    filename: Mapped[str] = mapped_column(index=True)
    original_filename: Mapped[str | None] = mapped_column(default=None)
    file_type: Mapped[str | None] = mapped_column(default=None)  # "pdf" | "txt"
    file_size: Mapped[int] = mapped_column(default=0)  # bytes
    content: Mapped[str] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(default=0)
    page_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="indexed")  # "processing"|"indexed"|"failed"
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    file_metadata: Mapped[str | None] = mapped_column("metadata", Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped["User | None"] = relationship(back_populates="documents")


class UsageEvent(Base):
    """One row per LLM call — powers the admin usage dashboard."""

    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None)
    conversation_id: Mapped[str | None] = mapped_column(default=None)
    event_type: Mapped[str]  # "chat" | "agent" | "doc_upload"
    model: Mapped[str | None] = mapped_column(default=None)
    prompt_tokens: Mapped[int] = mapped_column(default=0)
    completion_tokens: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
