from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import UsageEvent


def record_usage(
    db: Session,
    user_id: Optional[str],
    conversation_id: Optional[str],
    event_type: str,
    latency_ms: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    """Log one LLM call for the admin usage dashboard (app/api/admin.py)."""
    db.add(
        UsageEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            model=settings.MODEL,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
    )
    db.commit()
