from sqlalchemy.orm import Session as DBSession
from app.models.session import Session
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import MessageResponse, SessionResponse
from app.agent.graph import agent
from app.agent.state import ChatState

# 每个 session 对应一个 Agent 内存状态
agent_states: dict[str, ChatState] = {}

# Agent 响应模板（key = phase 名）
PHASE_RESPONSES = {
    "greeting": "欢迎来到星云！请描述你的需求——你可以提新功能、改动现有功能，或者上传 PRD。",
    "collecting": "能具体说说你想实现什么目标吗？涉及哪些功能模块？",
    "clarifying": "了解了。有没有什么技术约束或偏好？比如技术栈、部署方式、性能要求？\n\n另外，**第一版明确不做什么？** 有什么是你可以接受推迟的？",
    "generating": "好的，已明确需求范围！请点击下方的「生成设计文档」按钮，我将为你生成完整的设计文档。",
}


def _build_confirm_content(summary: str, scope_list: list[str] | None) -> str:
    content = f"""我已经整理了你的需求，请确认以下范围是否准确：

## ✅ 需求摘要
{summary}

## ❌ 不做（Out of Scope）
"""
    if scope_list:
        for item in scope_list:
            content += f"- {item}\n"
    else:
        content += "- （暂未列出，你可补充）\n"
    content += "\n以上范围正确吗？你可以：\n- ✅ **确认** — 范围正确，开始生成设计文档\n- ✏️ **补充** — 我需要调整或补充内容"
    return content


class ChatService:
    @staticmethod
    def create_session(project_id: str, db: DBSession) -> SessionResponse:
        session = Session(project_id=project_id)
        db.add(session)
        db.commit()
        db.refresh(session)

        agent_states[session.id] = {
            "messages": [], "phase": "greeting",
            "req_summary": None, "out_of_scope": None,
            "project_id": project_id, "session_id": session.id,
        }
        return SessionResponse(
            id=session.id, project_id=session.project_id,
            status=session.status, created_at=session.created_at.isoformat(),
        )

    @staticmethod
    def get_sessions(project_id: str, db: DBSession) -> list[SessionResponse]:
        sessions = db.query(Session).filter(Session.project_id == project_id
            ).order_by(Session.created_at.desc()).all()
        return [SessionResponse(
            id=s.id, project_id=s.project_id, status=s.status,
            created_at=s.created_at.isoformat(),
        ) for s in sessions]

    @staticmethod
    def get_messages(session_id: str, db: DBSession) -> list[MessageResponse]:
        messages = db.query(Message).filter(Message.session_id == session_id
            ).order_by(Message.created_at.asc()).all()
        return [MessageResponse(
            id=m.id, role=m.role, content=m.content, phase=m.phase,
            created_at=m.created_at.isoformat(),
        ) for m in messages]

    @staticmethod
    def send_message(session_id: str, content: str, user: User,
                     db: DBSession) -> list[MessageResponse]:
        # 保存用户消息
        user_msg = Message(session_id=session_id, role="user", content=content)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 获取/初始化 Agent 状态
        if session_id not in agent_states:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise ValueError("Session not found")
            agent_states[session_id] = {
                "messages": [], "phase": "greeting",
                "req_summary": None, "out_of_scope": None,
                "project_id": session.project_id, "session_id": session_id,
            }

        state = agent_states[session_id]
        state["messages"].append({"role": "user", "content": content})

        # 运行 Agent — 只获取 phase 和 req_summary 的更新
        result = agent.invoke(state)

        new_phase = result.get("phase", state["phase"])
        new_summary = result.get("req_summary", state.get("req_summary"))

        # 根据新 phase 生成响应
        agent_responses = []
        if state["phase"] == "greeting" and new_phase != "greeting":
            # 首次响应：先发问候
            agent_responses.append(("greeting", PHASE_RESPONSES["greeting"]))

        if new_phase == "confirming":
            content = _build_confirm_content(
                new_summary or "",
                result.get("out_of_scope") or state.get("out_of_scope"),
            )
            agent_responses.append(("confirming", content))
        elif new_phase != state["phase"]:
            text = PHASE_RESPONSES.get(new_phase)
            if text:
                agent_responses.append((new_phase, text))
        elif new_phase == "collecting":
            agent_responses.append(("collecting", PHASE_RESPONSES["collecting"]))
        elif new_phase == "clarifying":
            agent_responses.append(("clarifying", PHASE_RESPONSES["clarifying"]))

        # 保存 Agent 响应
        for phase_label, text in agent_responses:
            agent_msg = Message(
                session_id=session_id, role="agent",
                content=text, phase=phase_label,
            )
            db.add(agent_msg)
        if agent_responses:
            db.commit()
            # 将响应加入内存状态
            all_user_msgs_plus_agent = state["messages"] + [
                {"role": "assistant", "content": r[1]} for r in agent_responses
            ]
            result["messages"] = all_user_msgs_plus_agent

        # 更新内存状态
        result["phase"] = new_phase
        result["req_summary"] = new_summary
        agent_states[session_id] = result

        return ChatService.get_messages(session_id, db)
