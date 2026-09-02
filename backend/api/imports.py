from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ingestion.worker import (
    ingestion_queue,
)
from backend.infrastructure.database import (
    get_session,
)
from backend.infrastructure.storage import (
    pdf_path,
)
from backend.papers.models import Paper
from backend.papers.schemas import PaperOut
from config import settings


router = APIRouter(
    prefix="/imports",
    tags=["imports"],
)


@router.post(
    "/local",
    response_model=PaperOut,
)
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(
        get_session
    ),
):
    if (
        file.content_type
        != "application/pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="仅支持 PDF 文件",
        )

    paper_id = str(
        uuid4()
    )

    destination = pdf_path(
        paper_id
    )

    size = 0

    try:
        with destination.open(
            "wb"
        ) as fp:
            while True:
                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                size += len(chunk)

                max_bytes = (
                    settings.max_pdf_mb
                    * 1024
                    * 1024
                )

                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "PDF 最大允许 "
                            f"{settings.max_pdf_mb} MB"
                        ),
                    )

                fp.write(chunk)

    except Exception:
        destination.unlink(
            missing_ok=True
        )
        raise

    filename = Path(
        file.filename or "paper.pdf"
    ).name

    paper = Paper(
        id=paper_id,
        title=Path(filename).stem,
        filename=filename,
        status="queued",
        file_size=size,
        source="local",
    )

    db.add(paper)

    await db.commit()
    await db.refresh(paper)

    await ingestion_queue.enqueue(
        paper.id
    )

    return paper