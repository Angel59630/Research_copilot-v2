from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


@dataclass(frozen=True)
class RagRuntimeContext:
    conversation_id: str

    scope_type: Literal[
        "paper",
        "group",
    ]

    scope_id: str

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


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    page_number: int
    text: str
    score: float