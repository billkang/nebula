from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseModel(BaseModel):
    """Base Pydantic model for all Nebula data models."""

    model_config = ConfigDict(from_attributes=True)
