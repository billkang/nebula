from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel


class LogEntry(BaseModel):
    level: Literal["debug", "info", "warning", "error", "critical"]
    message: str
    timestamp: datetime
    stack: Optional[str] = None


class LogResponse(BaseModel):
    accepted: bool = True
