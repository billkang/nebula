from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from app.agent.state import ChatState
from app.agent.nodes import greeting_node, collect_node, planning_node, generate_node


def entry_router(state: ChatState) -> str:
    """从 START 路由到正确的阶段处理器"""
    last_msg = state["messages"][-1] if state["messages"] else {}
    is_user_msg = isinstance(last_msg, dict) and last_msg.get("role") == "user"

    phase = state["phase"]

    # No new user message → don't run anything
    if not is_user_msg:
        return END

    # Map phase names to node names
    phase_node_map = {
        "greeting": "greeting",
        "collecting": "collect",
        "planning": "planning",
        "generating": "generate",
        "generated": "generate",
    }
    return phase_node_map.get(phase, END)


def build_agent() -> CompiledStateGraph:
    graph = StateGraph(ChatState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("collect", collect_node)
    graph.add_node("planning", planning_node)
    graph.add_node("generate", generate_node)

    # START → appropriate node based on current phase
    graph.add_conditional_edges(START, entry_router, {
        "greeting": "greeting",
        "collect": "collect",
        "planning": "planning",
        "generate": "generate",
        END: END,
    })

    # All nodes run once per turn and return to END
    graph.add_edge("greeting", END)
    graph.add_edge("collect", END)
    graph.add_edge("planning", END)
    graph.add_edge("generate", END)

    return graph.compile()


agent = build_agent()
