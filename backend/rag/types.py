from dataclasses import dataclass
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


@dataclass(frozen=True)
class ScopePaper:
    """本轮 RAG 可见的论文目录项。"""

    ref: str
    paper_id: str
    title: str
    authors: str | None


@dataclass(frozen=True)
class RagRuntimeContext:
    conversation_id: str

    scope_type: Literal[
        "paper",
        "group",
    ]

    scope_id: str
    scope_name: str

    available_papers: tuple[
        ScopePaper,
        ...,
    ]

    allowed_paper_ids: tuple[
        str,
        ...,
    ]

    request_id: str
    top_k: int


class RetrievePapersInput(
    BaseModel
):
    query: str

    paper_refs: list[str] | None = Field(
        default=None,
        description=(
            "仅当用户明确指定当前目录中的"
            "一篇或多篇论文时，传入 P1、P2 "
            "等临时编号；用户未指定论文时省略，"
            "以检索整个当前范围。"
        ),
    )


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    page_number: int
    text: str
    score: float