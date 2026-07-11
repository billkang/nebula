from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    change_name: str | None = None
    created_at: str
    updated_at: str
