from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import (
    BaseModel,
    Field,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.infrastructure.database import (
    get_session,
)

from backend.ingestion.arxiv import (
    import_arxiv_paper,
    search_arxiv,
)

from backend.papers.schemas import (
    PaperOut,
)


router = APIRouter(
    prefix="/arxiv",
    tags=["arxiv"],
)


class ArxivSearchItem(
    BaseModel
):
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str | None
    categories: list[str]


class ArxivImportRequest(
    BaseModel
):
    value: str = Field(
        min_length=1
    )


@router.get(
    "/search",
    response_model=
        list[ArxivSearchItem],
)
async def search(
    q: str = Query(
        min_length=1
    ),

    start: int = Query(
        default=0,
        ge=0,
    ),

    max_results: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    return await search_arxiv(
        q,
        start=start,
        max_results=max_results,
    )


@router.post(
    "/import",
    response_model=
        PaperOut,
)
async def import_paper(
    payload:
        ArxivImportRequest,

    db: AsyncSession = Depends(
        get_session
    ),
):
    try:

        return (
            await
            import_arxiv_paper(
                db,
                payload.value.strip(),
            )
        )

    except (
        LookupError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc