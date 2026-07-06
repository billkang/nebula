from pydantic import BaseModel
from typing import Optional


class ExecuteStatus(BaseModel):
    status: str  # idle | running | success | failed
    message: Optional[str] = None
