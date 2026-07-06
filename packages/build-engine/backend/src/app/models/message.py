import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import TEXT
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(10), nullable=False)  # user | agent
    content = Column(Text, nullable=False)
    phase = Column(String(20), nullable=True)  # greeting | collecting | clarifying | confirming | generating
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
