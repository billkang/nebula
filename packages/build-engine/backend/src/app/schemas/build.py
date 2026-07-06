from pydantic import BaseModel
from typing import Optional


class BuildStatus(BaseModel):
    status: str  # idle | testing | verifying | packaging | success | failed
    message: Optional[str] = None


class ArtifactInfo(BaseModel):
    version: str
    created_at: str
    path: str
