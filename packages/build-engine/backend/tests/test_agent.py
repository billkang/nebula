"""Agent 单元测试 — 覆盖旅游助手流程"""
from unittest.mock import patch

from langgraph.graph import END
from app.agent.graph import entry_router
from app.agent.nodes import greeting_node, collect_node, planning_node, generate_node
from app.agent.state import ChatState


def _state(messages: list | None = None, phase: str = "collecting",
           req_summary: str | None = None,
           travel_plan: str | None = None) -> ChatState:
    return {
        "messages": messages or [],
        "phase": phase,
        "req_summary": req_summary,
        "out_of_scope": None,
        "project_id": None,
        "session_id": None,
        "response_content": None,
        "travel_plan": travel_plan,
    }


# ── entry_router ──────────────────────────────────────────────────────


def test_router_no_user_msg_ends():
    """最后一条消息不是用户消息 → END"""
    st = _state([{"role": "assistant", "content": "你好"}], phase="collecting")
    assert entry_router(st) == END


def test_router_user_msg_routes_by_phase():
    """用户消息 → 按 phase 路由到对应节点"""
    st = _state([{"role": "user", "content": "帮我规划旅游"}], phase="collecting")
    assert entry_router(st) == "collect"

    st2 = _state([{"role": "user", "content": "已准备好"}], phase="planning")
    assert entry_router(st2) == "planning"

    st3 = _state([{"role": "user", "content": "继续"}], phase="generating")
    assert entry_router(st3) == "generate"


def test_router_empty_messages():
    """无消息 → END"""
    st = _state([], phase="collecting")
    assert entry_router(st) == END


# ── greeting_node ─────────────────────────────────────────────────────

def test_greeting_node_pass_through():
    """greeting_node 是直通节点（欢迎语已在 create_session 中预存）"""
    st = _state([], phase="greeting")
    result = greeting_node(st)
    assert result["phase"] == "collecting"
    assert "messages" not in result  # 不应追加任何消息


# ── collect_node ──────────────────────────────────────────────────────

def test_collect_node_returns_response():
    """collect_node 应返回 LLM 响应内容"""
    st = _state([{"role": "user", "content": "我想去北京玩三天，预算5000"}], phase="collecting")
    with patch("app.agent.nodes._safe_call_llm") as mock_llm:
        mock_llm.return_value = "好的，信息已完整！准备为您生成北京三日游规划。"
        result = collect_node(st)
    assert "response_content" in result
    assert result["phase"] == "planning"  # LLM 表示信息完整 → 转 planning


# ── planning_node ─────────────────────────────────────────────────────

def test_planning_node_generates_travel_plan():
    """planning_node 生成旅游规划并存储到 travel_plan"""
    st = _state([
        {"role": "assistant", "content": "请告诉我你的出行信息"},
        {"role": "user", "content": "去北京，3天，预算5000"},
    ], phase="planning")
    with patch("app.agent.nodes._safe_call_llm") as mock_llm:
        mock_llm.return_value = "## 📍 北京\n三日游行程..."
        result = planning_node(st)
    assert result["phase"] == "generating"
    assert "travel_plan" in result
    assert result["travel_plan"]  # 不应为空
    assert "response_content" in result


# ── generate_node ─────────────────────────────────────────────────────

def test_generate_node_with_travel_plan():
    """有 travel_plan 时输出规划"""
    plan = "## 北京三日游\nDay 1: 故宫\n..."
    st = _state([], phase="generating", travel_plan=plan)
    result = generate_node(st)
    assert result["phase"] == "generated"
    assert result["response_content"] == plan


def test_generate_node_no_travel_plan():
    """无 travel_plan 时回退到 planning 阶段"""
    st = _state([], phase="generating", travel_plan=None)
    result = generate_node(st)
    assert result["phase"] == "planning"
    assert "response_content" in result


# ── entry_router unknown phase ────────────────────────────────────────

def test_router_unknown_phase():
    """未知 phase 路由到 END"""
    st = _state([{"role": "user", "content": "hi"}], phase="unknown_phase")
    assert entry_router(st) == END
