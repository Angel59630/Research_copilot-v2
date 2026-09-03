from fastapi import (
    APIRouter,
)

from backend.api.health import (
    router as health_router,
)

from backend.api.imports import (
    router as imports_router,
)

from backend.api.papers import (
    router as papers_router,
)

from backend.api.groups import (
    router as groups_router,
)

from backend.api.conversations import (
    router as conversations_router,
)

from backend.api.arxiv import (
    router as arxiv_router,
)


api_router = APIRouter()


api_router.include_router(
    health_router,
)


api_router.include_router(
    imports_router,
    prefix="/api",
)


api_router.include_router(
    papers_router,
    prefix="/api",
)


api_router.include_router(
    groups_router,
    prefix="/api",
)


api_router.include_router(
    conversations_router,
    prefix="/api",
)


api_router.include_router(
    arxiv_router,
    prefix="/api",
)