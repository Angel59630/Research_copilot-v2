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
from backend.papers.models import Paper
from backend.rag.types import (
    RagRuntimeContext,
    RetrievedChunk,
    RetrievePapersInput,
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
) -> tuple[
    str,
    list[RetrievedChunk],
]:
    """
    Retrieve relevant chunks from the
    papers allowed by the current runtime.
    """

    context = runtime.context

    allowed_paper_ids = (
        context.allowed_paper_ids
    )

    if not allowed_paper_ids:
        return (
            "当前范围没有可检索论文。",
            [],
        )

    query_vector = (
        await embedding_client().aembed_query(
            query
        )
    )

    result = collection().query(
        query_embeddings=[
            query_vector
        ],
        n_results=context.top_k,
        where={
            "paper_id": {
                "$in": list(
                    allowed_paper_ids
                )
            }
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
                titles[
                    paper_id
                ] = paper.title

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