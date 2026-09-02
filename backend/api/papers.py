from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import (
    FileResponse,
)
from uuid import UUID
from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.infrastructure.database import (
    get_session,
)
from backend.infrastructure.storage import (
    delete_paper_files,
    pdf_path,
)
from backend.infrastructure.vector_store import (
    delete_paper_vectors,
)
from backend.papers.models import Paper
from backend.papers.schemas import (
    PaperOut,
    PaperUpdate,
)


router = APIRouter(
    prefix="/papers",
    tags=["papers"],
)


@router.get("")
async def list_papers(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(
        get_session
    ),
):
    filters = []

    if q:
        filters.append(
            or_(
                Paper.title.ilike(
                    f"%{q}%"
                ),
                Paper.authors.ilike(
                    f"%{q}%"
                ),
            )
        )

    if status:
        filters.append(
            Paper.status == status
        )

    count_stmt = select(
        func.count(Paper.id)
    )

    if filters:
        count_stmt = (
            count_stmt.where(
                *filters
            )
        )

    total = await db.scalar(
        count_stmt
    )

    stmt = select(Paper)

    if filters:
        stmt = stmt.where(
            *filters
        )

    stmt = (
        stmt
        .order_by(
            Paper.created_at.desc()
        )
        .offset(
            (page - 1)
            * page_size
        )
        .limit(page_size)
    )

    result = await db.execute(
        stmt
    )

    papers = (
        result.scalars().all()
    )

    return {
        "items": [
            PaperOut.model_validate(
                paper
            )
            for paper in papers
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{paper_id}",
    response_model=PaperOut,
)
async def get_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(
        get_session
    ),
):
    paper_id_text = str(paper_id)

    paper = await db.get(
        Paper,
        paper_id_text,
    )

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="论文不存在",
        )

    return paper


@router.patch(
    "/{paper_id}",
    response_model=PaperOut,
)
async def update_paper(
    paper_id: UUID,
    payload: PaperUpdate,
    db: AsyncSession = Depends(
        get_session
    ),
):
    paper_id_text = str(paper_id)

    paper = await db.get(
        Paper,
        paper_id_text,
    )

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="论文不存在",
        )

    values = payload.model_dump(
        exclude_unset=True
    )

    for key, value in values.items():
        setattr(
            paper,
            key,
            value,
        )

    await db.commit()
    await db.refresh(paper)

    return paper


@router.get(
    "/{paper_id}/pdf"
)
async def download_pdf(
    paper_id: UUID,
    db: AsyncSession = Depends(
        get_session
    ),
):
    paper_id_text = str(paper_id)

    paper = await db.get(
        Paper,
        paper_id_text,
    )

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="论文不存在",
        )

    path = pdf_path(
        paper_id_text
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF 文件不存在",
        )

    return FileResponse(
        path=path,
        filename=paper.filename,
        media_type="application/pdf",
    )


@router.delete(
    "/{paper_id}",
    status_code=204,
)
async def delete_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(
        get_session
    ),
):
    paper_id_text = str(paper_id)

    paper = await db.get(
        Paper,
        paper_id_text,
    )

    # 幂等删除
    if paper is None:
        return

    paper.status = "deleting"

    await db.commit()

    try:
        delete_paper_vectors(
            paper_id_text
        )

        delete_paper_files(
            paper_id_text
        )

        await db.delete(
            paper
        )

        await db.commit()

    except Exception:
        paper.status = (
            "delete_failed"
        )

        await db.commit()

        raise
