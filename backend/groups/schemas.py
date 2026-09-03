from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class GroupCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    name: str
    description: str | None

    created_at: datetime
    updated_at: datetime