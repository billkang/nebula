from langgraph.graph import StateGraph, START, END
from app.agent.state import ChatState
from app.agent.nodes import greeting_node, collect_node, clarify_node, confirm_node, generate_node

CONFIRM_KW = ["确认", "正确", "没问题", "可以", "是的", "对", "ok", "yes", "confirm", "✅"]
REVISE_KW = ["修改", "调整", "补充", "不对", "不是", "遗漏", "加上", "添加", "少"]


def entry_router(state: ChatState) -> str:
    """从 START 路由到正确的阶段处理器"""
    last_msg = state["messages"][-1] if state["messages"] else {}
    is_user_msg = isinstance(last_msg, dict) and last_msg.get("role") == "user"
    content = last_msg.get("content", "") if isinstance(last_msg, dict) else ""

    phase = state["phase"]

    # greeting → 未发送过欢迎消息时才处理
    if phase == "greeting":
        has_greeting = any(
            m.get("role") == "assistant" and "欢迎来到星云" in m.get("content", "")
            for m in state["messages"]
        )
        if not has_greeting:
            return "greeting"
        return "collect" if is_user_msg else END

    # 无用户新消息时停止
    if not is_user_msg:
        return END

    # confirming: 判断用户确认/修改意图
    if phase == "confirming":
        if any(kw in content.lower() for kw in CONFIRM_KW):
            return "generate"
        elif any(kw in content.lower() for kw in REVISE_KW):
            return "collect"
        return "confirm"

    return phase  # collecting / clarifying → 对应 node


def build_agent() -> StateGraph:
    graph = StateGraph(ChatState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("collect", collect_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("generate", generate_node)

    # START → 合适的 node
    graph.add_conditional_edges(START, entry_router, {
        "greeting": "greeting", "collecting": "collect",
        "clarifying": "clarify", "confirming": "confirm",
        "collect": "collect", "confirm": "confirm", "generate": "generate",
        END: END,
    })

    # 所有 node 执行完后回到 END（每轮只处理一条消息）
    graph.add_edge("greeting", END)
    graph.add_edge("collect", END)
    graph.add_edge("clarify", END)
    graph.add_edge("confirm", END)
    graph.add_edge("generate", END)

    return graph.compile()


agent = build_agent()
