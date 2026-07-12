from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    level: Literal["debug", "info", "warning", "error", "critical"]
    message: str = Field(default="", max_length=4096)
    timestamp: datetime
    stack: Optional[str] = Field(default=None, max_length=16384)


class LogResponse(BaseModel):
    accepted: bool = True
