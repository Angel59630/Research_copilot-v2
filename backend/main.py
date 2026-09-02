from contextlib import (
    asynccontextmanager,
)

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.api.router import (
    api_router,
)
from backend.ingestion.worker import (
    ingestion_queue,
    mark_interrupted_ingestions,
)
from backend.infrastructure.errors import (
    register_exception_handlers,
)
from backend.infrastructure.logging import (
    setup_logging,
)
from backend.infrastructure.request_id import (
    RequestIdMiddleware,
)
from config import settings


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    settings.data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.log_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.chroma_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.papers_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    setup_logging()

    await mark_interrupted_ingestions()

    await ingestion_queue.start()

    try:
        yield

    finally:
        await ingestion_queue.stop()


app = FastAPI(
    title="Research Copilot",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    RequestIdMiddleware
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "Content-Disposition",
    ],
)


app.include_router(
    api_router
)


register_exception_handlers(app)
