from typing import Any
from app.agent.state import ChatState


def greeting_node(state: ChatState) -> dict:
    """问候阶段 — 欢迎用户并引导描述需求"""
    for m in state["messages"]:
        if m.get("role") == "assistant" and "欢迎来到星云" in m.get("content", ""):
            return {"phase": "collecting"}
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": "欢迎来到星云！请描述你的需求——你可以提新功能、改动现有功能，或者上传 PRD。"}],
        "phase": "collecting",
    }


def collect_node(state: ChatState) -> dict:
    """收集需求阶段 — 追问核心信息。消息足够详细 → 转 clarifying"""
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    if len(last_user_msg) > 50:
        # 消息足够详细 → 不用追问了，转 clarifying
        # 但先记录 summary
        summary = state.get("req_summary") or f"用户需求：{last_user_msg[:200]}"
        return {"phase": "clarifying", "req_summary": summary}

    has_asked = any(
        m.get("role") == "assistant" and "具体说说" in m.get("content", "")
        for m in state["messages"]
    )
    if has_asked:
        return {"phase": "collecting"}

    return {
        "messages": state["messages"] + [{"role": "assistant", "content": "能具体说说你想实现什么目标吗？涉及哪些功能模块？"}],
        "phase": "collecting",
    }


def clarify_node(state: ChatState) -> dict:
    """澄清细节阶段 — 追问模糊点"""
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    current_summary = state.get("req_summary", "")
    if last_user_msg and len(last_user_msg) > 10:
        current_summary += f"\n补充：{last_user_msg[:200]}"

    user_msg_count = sum(1 for m in state["messages"] if m.get("role") == "user")
    if user_msg_count >= 3:
        return {"phase": "confirming", "req_summary": current_summary}

    has_asked = any(
        m.get("role") == "assistant" and "不做什么" in m.get("content", "")
        for m in state["messages"]
    )
    if has_asked:
        return {"req_summary": current_summary, "phase": "clarifying"}

    return {
        "messages": state["messages"] + [{"role": "assistant", "content": "了解了。有没有什么技术约束或偏好？比如技术栈、部署方式、性能要求？\n\n另外，**第一版明确不做什么？** 有什么是你可以接受推迟的？"}],
        "req_summary": current_summary,
        "phase": "clarifying",
    }


def confirm_node(state: ChatState) -> dict:
    """确认范围阶段 — 展示摘要请求确认"""
    has_shown = any(
        m.get("role") == "assistant" and "需求摘要" in m.get("content", "")
        for m in state["messages"]
    )
    if has_shown:
        return {"phase": "confirming"}

    summary = state.get("req_summary", "")
    scope_list = state.get("out_of_scope", [])

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

    return {
        "messages": state["messages"] + [{"role": "assistant", "content": content}],
        "phase": "confirming",
    }


def generate_node(state: ChatState) -> dict:
    """生成文档阶段 — 通知用户可触发文档生成"""
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": "好的，已明确需求范围！请点击下方的「生成设计文档」按钮，我将为你生成完整的设计文档。"}],
        "phase": "generating",
    }
