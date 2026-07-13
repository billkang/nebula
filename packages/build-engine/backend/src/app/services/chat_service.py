import logging
import time
from pathlib import Path
from sqlalchemy.orm import Session as DBSession
from app.models.session import Session
from app.models.message import Message
from app.models.project import Project
from app.models.user import User
from app.schemas.chat import MessageResponse, SessionResponse
from app.agent.graph import agent
from app.agent.state import ChatState
from app.services.event_bus import get_event_bus
from app.services.doc_service import DocService
from app.utils.project_path import get_projects_base
from app.core.logging import biz_step, biz_stage_start, biz_stage_end

logger = logging.getLogger(__name__)

# 每个 session 对应一个 Agent 内存状态
agent_states: dict[str, ChatState] = {}

# Agent 响应兜底模板（当 LLM 不可用时使用）
PHASE_RESPONSES = {
    "greeting": "欢迎来到星云！请描述你的需求——你可以提新功能、改动现有功能，或者上传 PRD。",
    "collecting": "能具体说说你想做什么吗？涉及哪些功能模块？",
    "planning": "好的，信息已收集完毕，正在为你生成方案...",
    "generating": "方案已生成完毕。",
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


def _generate_project_files(project_id: str, req_summary: str | None,
                             travel_plan: str | None, db: DBSession) -> None:
    """Generate project files when the agent reaches the 'generated' phase.

    Writes conversation context and plan to the project directory,
    then attempts to generate SDD docs via DocService.
    Failures are logged but do not raise — the chat flow should not break.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning("generate_project_files: project %s not found", project_id)
        return
    if not project.change_name:
        logger.warning("generate_project_files: project %s has no change_name", project_id)
        return
    user = db.query(User).filter(User.id == project.owner_id).first()
    if not user:
        logger.warning("generate_project_files: owner not found for project %s", project_id)
        return

    project_dir = get_projects_base() / f"{user.username}-{project.change_name}"
    if not project_dir.exists():
        logger.warning("generate_project_files: project dir %s does not exist", project_dir)
        return

    biz_stage_start("PROJECT_FILE_GEN", project_id=project_id)

    # 1. Write conversation_context.md
    context_path = project_dir / "conversation_context.md"
    try:
        with open(context_path, "w", encoding="utf-8") as f:
            f.write("# 项目需求文档\n\n")
            f.write(f"## 项目名称\n\n{project.name}\n\n")
            if req_summary:
                f.write(f"## 需求摘要\n\n{req_summary}\n\n")
            if travel_plan:
                f.write(f"## 技术方案\n\n{travel_plan}\n\n")
        biz_step("PROJECT_FILE_GEN", "write-context")
        logger.info("Generated conversation_context.md for project %s", project_id)
    except OSError as e:
        logger.error("Failed to write conversation_context.md: %s", e)
        biz_step("PROJECT_FILE_GEN", "write-context-error", error=str(e))

    # 2. Try to generate SDD docs via DocService
    try:
        result = DocService.generate_docs(
            project_id, db,
            req_summary=req_summary or "",
            out_of_scope=[],
        )
        if result.get("success"):
            biz_step("PROJECT_FILE_GEN", "sdd-docs-ok")
            logger.info("SDD docs generated for project %s", project_id)
        else:
            biz_step("PROJECT_FILE_GEN", "sdd-docs-warn", message=result.get("message", ""))
            logger.warning("SDD doc generation returned: %s", result.get("message"))
    except Exception as e:
        logger.error("SDD doc generation failed (non-fatal): %s", e, exc_info=True)
        biz_step("PROJECT_FILE_GEN", "sdd-docs-error", error=str(e))

    biz_stage_end("PROJECT_FILE_GEN", status="done", project_id=project_id)


class ChatService:
    @staticmethod
    def create_session(project_id: str, db: DBSession) -> SessionResponse:
        session = Session(project_id=project_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info("Session created: id=%s project=%s", session.id, project_id)

        # Pre-save greeting so the frontend sees it immediately on page load
        greeting_text = "欢迎来到星云！请描述你的需求——你可以提新功能、改动现有功能，或者上传 PRD。"
        greeting_msg = Message(
            session_id=session.id, role="agent",
            content=greeting_text, phase="greeting",
        )
        db.add(greeting_msg)
        db.commit()

        agent_states[session.id] = {
            "messages": [{"role": "assistant", "content": greeting_text}],
            "phase": "collecting",
            "req_summary": None, "out_of_scope": None,
            "project_id": project_id, "session_id": session.id,
            "response_content": None,
            "travel_plan": None,
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
        t0 = time.time()
        logger.info("send_message: session=%s user=%s content_len=%d",
                     session_id, user.username, len(content))
        biz_stage_start("SEND_MESSAGE", session_id=session_id, user=user.username)

        # 保存用户消息
        user_msg = Message(session_id=session_id, role="user", content=content)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
        logger.debug("User message saved: id=%s", user_msg.id)

        # 获取/初始化 Agent 状态
        if session_id not in agent_states:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise ValueError("Session not found")
            agent_states[session_id] = {
                "messages": [], "phase": "greeting",
                "req_summary": None, "out_of_scope": None,
                "project_id": session.project_id, "session_id": session_id,
                "response_content": None, "travel_plan": None,
            }
            logger.info("Agent state initialized for session %s", session_id)

        state = agent_states[session_id]
        state["messages"].append({"role": "user", "content": content})

        # 运行 Agent
        t1 = time.time()
        result = agent.invoke(state)
        t2 = time.time()
        logger.info("Agent invoke completed: phase=%s->%s duration=%dms",
                     state["phase"], result.get("phase", state["phase"]),
                     int((t2 - t1) * 1000))

        new_phase = result.get("phase", state["phase"])
        response_content = result.get("response_content")

        # Log agent phase transitions
        if new_phase != state["phase"]:
            biz_step("AGENT_PHASE", "transition",
                     session_id=session_id,
                     project_id=state.get("project_id", "unknown"),
                     from_phase=state["phase"],
                     to_phase=new_phase)
            logger.info("Phase transition: %s -> %s", state["phase"], new_phase)

        new_summary = result.get("req_summary", state.get("req_summary"))

        # When phase becomes "generated", trigger project file generation
        if new_phase == "generated":
            pid = state.get("project_id", "")
            if pid:
                _generate_project_files(
                    project_id=pid,
                    req_summary=new_summary,
                    travel_plan=result.get("travel_plan") or state.get("travel_plan"),
                    db=db,
                )

        # 根据 new_phase 和 LLM response_content 生成响应
        agent_responses: list[tuple[str, str]] = []

        if new_phase != state["phase"]:
            # 阶段变化 → 使用 LLM 响应或阶段兜底模板
            text = response_content or PHASE_RESPONSES.get(new_phase)
            if text:
                agent_responses.append((new_phase, text))
        elif response_content is not None:
            # 阶段未变化但有 LLM 响应 → 使用 LLM 响应或兜底模板
            text = response_content or PHASE_RESPONSES.get(new_phase, "")
            if text:
                agent_responses.append((new_phase, text))

        # 保存 Agent 响应
        for phase_label, text in agent_responses:
            agent_msg = Message(
                session_id=session_id, role="agent",
                content=text, phase=phase_label,
            )
            db.add(agent_msg)
        if agent_responses:
            db.commit()
            logger.info("Agent responses saved: count=%d phases=%s",
                         len(agent_responses),
                         [r[0] for r in agent_responses])
            # 将响应加入内存状态
            all_user_msgs_plus_agent = state["messages"] + [
                {"role": "assistant", "content": r[1]} for r in agent_responses
            ]
            result["messages"] = all_user_msgs_plus_agent

        # 更新内存状态
        result["phase"] = new_phase
        result["req_summary"] = new_summary
        result["travel_plan"] = result.get("travel_plan") or state.get("travel_plan")
        agent_states[session_id] = result

        # Notify SSE connections
        get_event_bus().notify(session_id)
        logger.debug("SSE notified for session %s", session_id)

        td = time.time() - t0
        biz_stage_end("SEND_MESSAGE", status="ok",
                       session_id=session_id, duration_ms=int(td * 1000))
        logger.info("send_message done: session=%s duration=%dms",
                     session_id, int(td * 1000))

        return ChatService.get_messages(session_id, db)
