import asyncio
import json
import logging

from sqlalchemy import select

from backend.ingestion.chunker import (
    chunk_page,
)
from backend.ingestion.pdf_parser import (
    PdfValidationError,
    parse_pdf,
)
from backend.infrastructure.database import (
    SessionFactory,
)
from backend.infrastructure.storage import (
    pages_path,
    pdf_path,
)
from backend.infrastructure.vector_store import (
    add_chunks,
    delete_paper_vectors,
)
from backend.papers.models import Paper
from config import settings


logger = logging.getLogger(__name__)


class IngestionQueue:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = (
            asyncio.Queue()
        )

        self.tasks: list[
            asyncio.Task
        ] = []

    async def start(self) -> None:
        for _ in range(
            settings.ingestion_workers
        ):
            task = asyncio.create_task(
                self._worker()
            )

            self.tasks.append(task)

    async def stop(self) -> None:
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(
            *self.tasks,
            return_exceptions=True,
        )

        self.tasks.clear()

    async def enqueue(
        self,
        paper_id: str,
    ) -> None:
        await self.queue.put(
            paper_id
        )

    async def _worker(self) -> None:
        while True:
            paper_id = (
                await self.queue.get()
            )

            try:
                await self._process(
                    paper_id
                )

            except asyncio.CancelledError:
                raise

            except Exception:
                logger.exception(
                    "paper ingestion failed",
                    extra={
                        "paper_id": paper_id,
                    },
                )

            finally:
                self.queue.task_done()

    async def _process(
        self,
        paper_id: str,
    ) -> None:
        async with SessionFactory() as db:
            paper = await db.get(
                Paper,
                paper_id,
            )

            if paper is None:
                return

            try:
                paper.status = "parsing"
                paper.error_message = None

                await db.commit()

                output_path = pages_path(
                    paper_id
                )

                page_count = (
                    await asyncio.to_thread(
                        parse_pdf,
                        pdf_path(paper_id),
                        output_path,
                    )
                )

                paper.page_count = (
                    page_count
                )

                paper.status = "embedding"

                await db.commit()

                # 重试之前先删除旧向量
                delete_paper_vectors(
                    paper_id
                )

                chunks = []

                with output_path.open(
                    "r",
                    encoding="utf-8",
                ) as fp:
                    for line in fp:
                        record = (
                            json.loads(line)
                        )

                        page_chunks = (
                            chunk_page(
                                paper_id=paper_id,
                                page_number=(
                                    record[
                                        "page_number"
                                    ]
                                ),
                                text=record["text"],
                                chunk_size=(
                                    settings.chunk_size
                                ),
                                overlap=(
                                    settings.chunk_overlap
                                ),
                            )
                        )

                        chunks.extend(
                            page_chunks
                        )

                await add_chunks(chunks)

                paper.status = "ready"
                paper.error_message = None

                await db.commit()

            except PdfValidationError as exc:
                paper.status = "failed"
                paper.error_message = str(
                    exc
                )

                await db.commit()

            except Exception:
                paper.status = "failed"
                paper.error_message = (
                    "论文处理过程中发生错误"
                )

                await db.commit()

                raise


ingestion_queue = IngestionQueue()


async def mark_interrupted_ingestions() -> None:
    async with SessionFactory() as db:
        result = await db.execute(
            select(Paper).where(
                Paper.status.in_(
                    [
                        "parsing",
                        "embedding",
                    ]
                )
            )
        )

        papers = result.scalars().all()

        for paper in papers:
            paper.status = "interrupted"

        await db.commit()