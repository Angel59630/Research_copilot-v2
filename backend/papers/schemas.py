from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    authors: str | None
    filename: str
    status: str
    page_count: int | None
    created_at: datetime


class PaperUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    authors: str | None = None
    abstract: str | None = None


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None