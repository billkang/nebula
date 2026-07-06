from pydantic import BaseModel
from typing import Optional


class DocGenerateRequest(BaseModel):
    req_summary: Optional[str] = None
    out_of_scope: Optional[list[str]] = None


class DocInfo(BaseModel):
    type: str  # proposal | specs | design | tasks
    path: str
    exists: bool


class DocGenerateResponse(BaseModel):
    success: bool
    message: str
    docs: list[DocInfo]
