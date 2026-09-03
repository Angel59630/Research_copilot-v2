from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


MODEL_FIELDS = {
    "model_provider",
    "model_name",
}


def validate_model_pair(
    model_provider: str | None,
    model_name: str | None,
) -> None:
    if (
        (model_provider is None)
        != (model_name is None)
    ):
        raise ValueError(
            "模型提供方和模型名称"
            "必须同时提供"
        )


class ConversationCreate(BaseModel):
    scope_type: Literal[
        "paper",
        "group",
    ]
    scope_id: str

    title: str = Field(
        default="新会话",
        max_length=300,
    )

    model_provider: str | None = None
    model_name: str | None = None

    @field_validator(
        "model_provider",
        "model_name",
    )
    @classmethod
    def normalize_model_field(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "模型配置不能为空"
            )

        return value

    @model_validator(mode="after")
    def validate_model_selection(
        self,
    ):
        validate_model_pair(
            self.model_provider,
            self.model_name,
        )

        return self


class ConversationUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=300,
    )
    model_provider: str | None = None
    model_name: str | None = None

    @field_validator(
        "model_provider",
        "model_name",
    )
    @classmethod
    def normalize_model_field(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "模型配置不能为空"
            )

        return value

    @model_validator(mode="after")
    def validate_model_selection(
        self,
    ):
        submitted_fields = (
            MODEL_FIELDS
            & self.model_fields_set
        )

        if not submitted_fields:
            return self

        if (
            submitted_fields
            != MODEL_FIELDS
            or self.model_provider is None
            or self.model_name is None
        ):
            raise ValueError(
                "模型提供方和模型名称"
                "必须同时提供"
            )

        return self


class ConversationOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    title: str

    scope_type: str
    scope_id: str

    model_provider: str
    model_name: str

    supports_tool_calling: bool

    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "消息不能为空"
            )

        return value


class CitationOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    source_number: int

    paper_id: str
    paper_title: str
    page_number: int
    chunk_id: str


class MessageOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    role: str
    content: str
    sequence: int
    created_at: datetime

    citations: list[
        CitationOut
    ] = Field(
        default_factory=list
    )