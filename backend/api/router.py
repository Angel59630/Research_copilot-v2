from fastapi import APIRouter

from backend.api.health import router as health_router
from backend.api.imports import router as imports_router
from backend.api.papers import router as papers_router


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