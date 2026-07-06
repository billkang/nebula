from typing import TypedDict, Optional


class ChatState(TypedDict):
    messages: list  # list of dicts: {"role": "user"|"assistant", "content": str}
    phase: str  # greeting | collecting | clarifying | confirming | generating
    req_summary: Optional[str]
    out_of_scope: Optional[list[str]]
    project_id: Optional[str]
    session_id: Optional[str]
