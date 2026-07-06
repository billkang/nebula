from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.chat import MessageSend, MessageResponse, SessionResponse
from app.services.chat_service import ChatService

chat_router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["chat"])


@chat_router.get("", response_model=list[SessionResponse])
def list_sessions(project_id: str, db: DBSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return ChatService.get_sessions(project_id, db)


@chat_router.post("", response_model=SessionResponse)
def create_session(project_id: str, db: DBSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return ChatService.create_session(project_id, db)


@chat_router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: str, db: DBSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return ChatService.get_messages(session_id, db)


@chat_router.post("/{session_id}/messages", response_model=list[MessageResponse])
def send_message(session_id: str, req: MessageSend, db: DBSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    try:
        return ChatService.send_message(session_id, req.content, user, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
