from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.session import Session as SessionModel
from app.services.doc_service import DocService
from app.services.chat_service import agent_states

doc_router = APIRouter(prefix="/projects/{project_id}/docs", tags=["documents"])


@doc_router.get("")
def list_docs(project_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    return DocService.list_docs(project_id, db)


@doc_router.get("/{doc_type}")
def get_doc(project_id: int, doc_type: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    content = DocService.get_doc(project_id, doc_type, db)
    if content is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"type": doc_type, "content": content}


@doc_router.post("/generate")
def generate_docs(project_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    # 从项目最新 session 的 agent state 中提取上下文
    req_summary = None
    out_of_scope = None
    latest = db.query(SessionModel).filter(
        SessionModel.project_id == project_id,
    ).order_by(SessionModel.created_at.desc()).first()
    if latest and latest.id in agent_states:
        state = agent_states[latest.id]
        req_summary = state.get("req_summary")
        out_of_scope = state.get("out_of_scope")

    return DocService.generate_docs(
        project_id=project_id,
        db=db,
        req_summary=req_summary,
        out_of_scope=out_of_scope,
    )
