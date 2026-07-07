import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_sse
from app.models.user import User
from app.schemas.chat import MessageSend, MessageResponse, SessionResponse
from app.services.chat_service import ChatService
from app.services.event_bus import get_event_bus

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


@chat_router.get("/{session_id}/messages/stream")
async def stream_messages(
    session_id: str,
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user_sse),
):
    event_bus = get_event_bus()

    async def event_generator():
        loop = asyncio.get_running_loop()
        try:
            # 1. Initial push: current full message list
            messages = await loop.run_in_executor(
                None, lambda: ChatService.get_messages(session_id, db)
            )
            yield f"data: {json.dumps([m.model_dump() for m in messages], default=str)}\n\n"

            # 2. Wait loop: notify -> push, timeout -> heartbeat
            while True:
                try:
                    notified = await event_bus.wait(session_id, timeout=30)
                    if not notified:
                        yield ": heartbeat\n\n"
                        continue
                    messages = await loop.run_in_executor(
                        None, lambda: ChatService.get_messages(session_id, db)
                    )
                    yield f"data: {json.dumps([m.model_dump() for m in messages], default=str)}\n\n"
                except Exception as e:
                    db.rollback()  # Reset stale session before retry
                    yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
                    await asyncio.sleep(5)
        except GeneratorExit:
            event_bus.remove(session_id)
        except Exception:
            event_bus.remove(session_id)
            raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
