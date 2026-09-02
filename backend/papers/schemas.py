from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    authors: str | None
    abstract: str | None
    filename: str
    source: str
    status: str
    error_message: str | None
    page_count: int | None
    file_size: int | None
    created_at: datetime
    updated_at: datetime


class PaperUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    authors: str | None = None
    abstract: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str:
        if value is None or not value.strip():
            raise ValueError(
                "论文标题不能为空"
            )

        return value.strip()


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
