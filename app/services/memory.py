from sqlalchemy.orm import Session
from app.models import Conversation, Message
from typing import List, Dict

class MemoryService:
    def ensure_conversation(self, db: Session, conversation_id: str):
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            conv = Conversation(id=conversation_id)
            db.add(conv)
            db.commit()
        return conv
    
    def add_message(self, db: Session, conversation_id: str, role: str, content: str):
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        return message
    
    def get_history(self, db: Session, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        return [{"role": m.role, "content": m.content} for m in reversed(messages)]