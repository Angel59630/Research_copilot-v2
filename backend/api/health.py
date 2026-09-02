from fastapi import APIRouter

from config import settings


router = APIRouter(
    tags=["health"],
)


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "environment":
            settings.app_env,
        "embedding_model":
            settings.ollama_embed_model,
    }