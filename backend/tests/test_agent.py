"""Agent 单元测试 — 覆盖 entry_router 路由逻辑和各阶段节点函数"""
from langgraph.graph import END
from app.agent.graph import entry_router, CONFIRM_KW, REVISE_KW
from app.agent.nodes import greeting_node, collect_node, clarify_node, confirm_node, generate_node
from app.agent.state import ChatState


def _state(messages: list | None = None, phase: str = "greeting",
           req_summary: str | None = None,
           out_of_scope: list[str] | None = None) -> ChatState:
    return {
        "messages": messages or [],
        "phase": phase,
        "req_summary": req_summary,
        "out_of_scope": out_of_scope,
        "project_id": None,
        "session_id": None,
    }


# ── entry_router ──────────────────────────────────────────────────────

def test_router_greeting_no_welcome():
    """greeting 阶段且无欢迎消息 → 路由到 greeting node"""
    st = _state([{"role": "user", "content": "你好"}], phase="greeting")
    assert entry_router(st) == "greeting"


def test_router_greeting_has_welcome_no_user():
    """greeting 已有欢迎消息，最后一条是 assistant → END"""
    st = _state([{"role": "assistant", "content": "欢迎来到星云！请描述你的需求。"},
                  {"role": "user", "content": "我想做个功能"}],
                phase="greeting")
    assert entry_router(st) == "collect"


def test_router_greeting_has_welcome_assistant_last():
    """greeting 已有欢迎消息，最后一条是 assistant → END"""
    st = _state([{"role": "assistant", "content": "欢迎来到星云！请描述你的需求。"}],
                phase="greeting")
    assert entry_router(st) == END


def test_router_collecting_routes_to_collecting():
    st = _state([{"role": "user", "content": "我想加个登录功能"}], phase="collecting")
    assert entry_router(st) == "collecting"


def test_router_clarifying_routes_to_clarifying():
    st = _state([{"role": "user", "content": "用 JWT 认证"}], phase="clarifying")
    assert entry_router(st) == "clarifying"


def test_router_confirming_confirm_kw():
    for kw in CONFIRM_KW:
        st = _state([{"role": "user", "content": kw}], phase="confirming")
        assert entry_router(st) == "generate", f"KW '{kw}' 应路由到 generate"


def test_router_confirming_revise_kw():
    for kw in ("修改", "调整", "补充"):
        st = _state([{"role": "user", "content": kw}], phase="confirming")
        assert entry_router(st) == "collect", f"KW '{kw}' 应路由到 collect"


def test_router_confirming_other():
    st = _state([{"role": "user", "content": "让我想想"}], phase="confirming")
    assert entry_router(st) == "confirm"


def test_router_generating_no_user_msg():
    """generating 阶段无新用户消息 → END"""
    st = _state([{"role": "assistant", "content": "文档已生成"}], phase="generating")
    assert entry_router(st) == END


def test_router_generating_user_msg():
    """generating 阶段有用户新消息 → generating（兜底返回 phase）"""
    st = _state([{"role": "assistant", "content": "文档已生成"},
                  {"role": "user", "content": "好的"}],
                phase="generating")
    assert entry_router(st) == "generating"


# ── greeting_node ─────────────────────────────────────────────────────

def test_greeting_node_sends_welcome():
    st = _state([], phase="greeting")
    result = greeting_node(st)
    assert result["phase"] == "collecting"
    assert "欢迎来到星云" in result["messages"][-1]["content"]


def test_greeting_node_skips_if_already_welcomed():
    st = _state([{"role": "assistant", "content": "欢迎来到星云！请描述需求。"}], phase="greeting")
    result = greeting_node(st)
    assert "messages" not in result  # 不应追加重复欢迎语
    assert result["phase"] == "collecting"


# ── collect_node ──────────────────────────────────────────────────────

def test_collect_node_long_msg_transitions():
    """用户消息 > 50 字 → 转 clarifying"""
    msg = "我想实现一个用户注册登录功能，包含邮箱验证、密码重置和 JWT 认证。还有用户管理、角色权限分配和数据报表查看功能。"  # 60+ 字
    st = _state([{"role": "user", "content": msg}], phase="collecting")
    result = collect_node(st)
    assert result["phase"] == "clarifying"
    assert result.get("req_summary") is not None


def test_collect_node_short_msg_asks():
    """用户消息 <= 50 字且未追问过 → 追问"""
    st = _state([{"role": "user", "content": "你好"}], phase="collecting")
    result = collect_node(st)
    assert result["phase"] == "collecting"
    assert "具体说说" in result["messages"][-1]["content"]


# ── clarify_node ──────────────────────────────────────────────────────

def test_clarify_node_accumulates_summary():
    st = _state([{"role": "user", "content": "用 JWT 做认证，token 有效期设 24 小时"},
                  {"role": "user", "content": "还需要加密码重置功能和邮箱验证"}],
                phase="clarifying", req_summary="需求：登录")
    result = clarify_node(st)
    assert "补充：" in (result.get("req_summary") or "")
    assert result["phase"] in ("clarifying", "confirming")


def test_clarify_node_enough_messages_transitions():
    """用户消息 >= 3 条 → 转 confirming"""
    st = _state([{"role": "user", "content": "a"},
                  {"role": "user", "content": "b"},
                  {"role": "user", "content": "c"}],
                phase="clarifying", req_summary="一些需求")
    result = clarify_node(st)
    assert result["phase"] == "confirming"


# ── confirm_node ──────────────────────────────────────────────────────

def test_confirm_node_shows_summary():
    st = _state([], phase="confirming", req_summary="需求：登录功能")
    result = confirm_node(st)
    assert result["phase"] == "confirming"
    assert "需求摘要" in result["messages"][-1]["content"]
    assert "登录功能" in result["messages"][-1]["content"]


def test_confirm_node_already_shown():
    st = _state([{"role": "assistant", "content": "需求摘要如下"}], phase="confirming")
    result = confirm_node(st)
    assert "messages" not in result
    assert result["phase"] == "confirming"


# ── generate_node ─────────────────────────────────────────────────────

def test_generate_node():
    st = _state([], phase="generating")
    result = generate_node(st)
    assert result["phase"] == "generating"
    assert "生成设计文档" in result["messages"][-1]["content"]


# ── edge cases ────────────────────────────────────────────────────────

def test_router_empty_messages():
    """空对话 → greeting 节点"""
    st = _state([], phase="greeting")
    assert entry_router(st) == "greeting"


def test_router_not_user_msg():
    st = _state([{"role": "assistant", "content": "好的"}], phase="collecting")
    assert entry_router(st) == END

