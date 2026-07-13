"""Agent nodes for the LangGraph state machine.

Each node is a pure function that takes ChatState and returns state updates.
Nodes use the LLM (DeepSeek) for contextual natural language generation,
with fallback to hardcoded templates.
"""

import logging
from typing import Any
from app.agent.state import ChatState
from app.llm import get_llm_provider
from app.core.logging import biz_step

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompts per phase
# ---------------------------------------------------------------------------

_COLLECT_SYSTEM = """你是星云(Nebula)平台的AI需求分析助手。

职责：帮助用户梳理需求，判断信息是否足够清晰。

- 如果用户已经提供了足够的具体信息（功能描述、输入输出、关键特性等），认可用户的需求并告知用户准备生成。
- 如果信息模糊或缺失关键内容，针对性追问缺失的部分。
- 回复要自然、友好、有条理。

注意：如果用户的问题是其他话题，正常回答。"""

_PLANNING_SYSTEM = """你是星云(Nebula)平台的资深技术架构师。

职责：根据用户的需求描述，生成一份完整的技术方案。请输出以下两部分内容：

## 需求摘要
（3-5句话概括用户的核心需求，用中文）
（重要：此摘要将作为项目文档的需求说明）

## 技术方案
（包含以下结构）
- 项目概述
- 核心功能清单
- 技术方案（技术栈、架构、关键实现）
- 数据模型（核心数据结构和字段）
- API 接口（主要接口设计）

要求：内容专业、结构清晰、使用中文。"""


def _call_llm(state: ChatState, system_prompt: str) -> str:
    """Call the LLM provider and return the generated text.

    Returns empty string on failure; caller should fall back.
    """
    provider = get_llm_provider()
    # Build message list for the LLM — merge agent messages into assistant role
    llm_messages: list[dict[str, str]] = []
    for m in state["messages"]:
        role = "assistant" if m.get("role") in ("agent", "assistant") else "user"
        llm_messages.append({"role": role, "content": m.get("content", "")})

    biz_step("LLM_CALL", "start", msg_count=len(llm_messages))
    response = provider.chat(
        llm_messages,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096,
    )
    biz_step("LLM_CALL", "ok", response_length=len(response))
    return response


def _safe_call_llm(state: ChatState, system_prompt: str) -> str:
    """Call LLM with exception safety. Returns empty string on any failure."""
    try:
        return _call_llm(state, system_prompt)
    except Exception as e:
        logger.error("LLM call failed in node: %s", e, exc_info=True)
        biz_step("LLM_CALL", "error", error=str(e))
        return ""


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


def greeting_node(state: ChatState) -> dict[str, Any]:
    """Greeting — handled via pre-saved message; this node is a pass-through."""
    return {"phase": "collecting"}


def _get_last_user_message(state: ChatState) -> str:
    """Extract the last user message content from state."""
    for msg in reversed(state["messages"]):
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def _user_says_go_ahead(state: ChatState) -> bool:
    """Check if the user explicitly signals intent to proceed.

    When the user says '开始吧', '开发吧', '确认', etc.,
    it means they're ready for the agent to start generating.
    """
    user_msg = _get_last_user_message(state)
    go_ahead_keywords = [
        "开始吧", "开发吧", "可以", "可以了", "开始",
        "确认", "确认没问题", "没问题", "就这样",
        "动手吧", "生成吧", "好的", "好",
        "go ahead", "start", "proceed", "yes",
    ]
    for kw in go_ahead_keywords:
        if user_msg.strip() == kw or user_msg.strip().rstrip("。！!") == kw:
            return True
    # Also check standalone affirmatives
    if user_msg.strip() in ("可以", "可以。", "可以！", "行", "行。", "好", "好。", "好的"):
        return True
    return False


def collect_node(state: ChatState) -> dict[str, Any]:
    """Collect requirements — ask follow-ups or confirm when enough info.

    Uses the LLM to generate a contextual response.
    Falls back to a hardcoded prompt when LLM is unavailable.
    """
    # If the user explicitly says to proceed, jump to planning directly
    if _user_says_go_ahead(state):
        return {
            "phase": "planning",
            "response_content": "好的，需求已明确，正在为你生成技术方案...",
        }

    response = _safe_call_llm(state, _COLLECT_SYSTEM)
    if not response:
        response = "能具体说说你想做什么吗？涉及哪些功能模块？"

    # Check if LLM response indicates info is complete enough for planning
    ready_keywords = ["准备生成", "准备为您", "已收集完毕", "准备开始", "生成技术方案"]
    is_ready = any(kw in (response or "") for kw in ready_keywords)

    if is_ready:
        return {
            "phase": "planning",
            "response_content": response,
        }

    return {
        "phase": "collecting",
        "response_content": response,
    }


def _extract_summary(plan_text: str) -> tuple[str, str]:
    """Split LLM output into (req_summary, full_plan).

    Looks for "## 技术方案" marker; everything before it (minus the
    summary header) is the summary, everything from it onward is the plan.
    If no marker found, use first 200 chars as summary and full text as plan.
    """
    plan_marker = "## 技术方案"
    if plan_marker in plan_text:
        summary_part, plan_part = plan_text.split(plan_marker, 1)
        # Clean up summary: remove its own header and strip whitespace
        summary_part = summary_part.replace("## 需求摘要", "").strip()
        return summary_part or plan_text[:200], plan_text
    return plan_text[:200], plan_text


def planning_node(state: ChatState) -> dict[str, Any]:
    """Generate the technical plan / design document using the LLM."""
    response = _safe_call_llm(state, _PLANNING_SYSTEM)

    summary, plan = _extract_summary(response or "")
    result: dict[str, Any] = {
        "phase": "generating",
        "response_content": response or "无法生成方案，请补充更多信息后重试。",
        "travel_plan": plan or "",
        "req_summary": summary or None,
    }

    return result


def generate_node(state: ChatState) -> dict[str, Any]:
    """Final node — output the generated plan."""
    plan = state.get("travel_plan") or ""

    if plan:
        return {
            "phase": "generated",
            "response_content": plan,
        }

    # Fallback: no plan yet — trigger planning
    return {
        "phase": "planning",
        "response_content": "信息不足，让我再问一些问题...",
    }
