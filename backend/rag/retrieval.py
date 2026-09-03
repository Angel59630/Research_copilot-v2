import logging

from langchain.tools import (
    ToolRuntime,
    tool,
)

from backend.infrastructure.database import (
    SessionFactory,
)
from backend.infrastructure.vector_store import (
    collection,
    embedding_client,
)
from backend.papers.models import (
    Paper,
)
from backend.rag.types import (
    RagRuntimeContext,
    RetrievedChunk,
    RetrievePapersInput,
)


logger = logging.getLogger(
    __name__
)


def resolve_requested_paper_ids(
    context: RagRuntimeContext,
    paper_refs: list[str] | None,
) -> tuple[
    tuple[str, ...],
    str | None,
]:
    """把本轮临时编号解析为范围内的论文 ID。"""

    if not paper_refs:
        return (
            context.allowed_paper_ids,
            None,
        )

    ref_to_id = {
        paper.ref: paper.paper_id
        for paper
        in context.available_papers
    }

    normalized_refs = tuple(
        dict.fromkeys(
            ref.strip().upper()
            for ref in paper_refs
            if (
                isinstance(ref, str)
                and ref.strip()
            )
        )
    )

    if not normalized_refs:
        return (
            context.allowed_paper_ids,
            None,
        )

    unknown_refs = tuple(
        ref
        for ref in normalized_refs
        if ref not in ref_to_id
    )

    if unknown_refs:
        return (
            (),
            (
                "指定的论文编号无效，"
                "请根据当前论文目录重新确认。"
            ),
        )

    allowed_ids = set(
        context.allowed_paper_ids
    )

    selected_ids = tuple(
        ref_to_id[ref]
        for ref in normalized_refs
        if ref_to_id[ref] in allowed_ids
    )

    if (
        len(selected_ids)
        != len(normalized_refs)
    ):
        return (
            (),
            (
                "指定的论文不在当前"
                "可检索范围内。"
            ),
        )

    return (
        selected_ids,
        None,
    )


@tool(
    args_schema=RetrievePapersInput,
    response_format=(
        "content_and_artifact"
    ),
)
async def retrieve_papers(
    query: str,
    runtime: ToolRuntime[
        RagRuntimeContext
    ],
    paper_refs: list[str] | None = None,
) -> tuple[
    str,
    list[RetrievedChunk],
]:
    """
    检索当前运行范围内允许访问的论文文本块。

    paper_refs 为空时检索整个范围；
    非空时只检索对应的论文子集。
    """

    context = runtime.context

    target_paper_ids, error = (
        resolve_requested_paper_ids(
            context,
            paper_refs,
        )
    )

    if error is not None:
        logger.warning(
            "RAG 检索论文编号校验失败",
            extra={
                "request_id":
                    context.request_id,

                "scope_type":
                    context.scope_type,

                "scope_id":
                    context.scope_id,

                "selection_mode":
                    "specified",

                "available_count":
                    len(
                        context
                        .allowed_paper_ids
                    ),

                "selected_count":
                    0,
            },
        )

        return (
            error,
            [],
        )

    if not target_paper_ids:
        return (
            "当前范围没有可检索论文。",
            [],
        )

    logger.info(
        "RAG 检索范围已确定",
        extra={
            "request_id":
                context.request_id,

            "scope_type":
                context.scope_type,

            "scope_id":
                context.scope_id,

            "selection_mode": (
                "specified"
                if paper_refs
                else "full_scope"
            ),

            "available_count":
                len(
                    context.allowed_paper_ids
                ),

            "selected_count":
                len(target_paper_ids),
        },
    )

    query_vector = (
        await embedding_client()
        .aembed_query(
            query
        )
    )

    result = collection().query(
        query_embeddings=[
            query_vector,
        ],
        n_results=context.top_k,
        where={
            "paper_id": {
                "$in": list(
                    target_paper_ids
                ),
            },
        },
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    ids = result["ids"][0]
    documents = (
        result["documents"][0]
    )
    metadatas = (
        result["metadatas"][0]
    )
    distances = (
        result["distances"][0]
    )

    paper_ids = {
        metadata["paper_id"]
        for metadata in metadatas
    }

    titles: dict[
        str,
        str,
    ] = {}

    async with SessionFactory() as db:
        for paper_id in paper_ids:
            paper = await db.get(
                Paper,
                paper_id,
            )

            if paper is not None:
                titles[paper_id] = (
                    paper.title
                )

    chunks: list[
        RetrievedChunk
    ] = []

    for (
        chunk_id,
        document,
        metadata,
        distance,
    ) in zip(
        ids,
        documents,
        metadatas,
        distances,
        strict=True,
    ):
        paper_id = metadata[
            "paper_id"
        ]

        page_number = int(
            metadata[
                "page_number"
            ]
        )

        score = (
            1.0
            - float(distance)
        )

        chunk = RetrievedChunk(
            chunk_id=chunk_id,
            paper_id=paper_id,
            paper_title=titles.get(
                paper_id,
                "Unknown paper",
            ),
            page_number=page_number,
            text=document,
            score=score,
        )

        chunks.append(chunk)

    content = "\n\n".join(
        (
            f"[{chunk.chunk_id}] "
            f"{chunk.paper_title}, "
            f"PDF page "
            f"{chunk.page_number}\n"
            f"{chunk.text}"
        )
        for chunk in chunks
    )

    return (
        content,
        chunks,
    )