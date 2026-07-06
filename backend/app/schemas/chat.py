from pydantic import BaseModel
from typing import Optional


class MessageSend(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    phase: Optional[str] = None
    created_at: str


class SessionResponse(BaseModel):
    id: str
    project_id: str
    status: str
    created_at: str
