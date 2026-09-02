from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str = (
        "sqlite+aiosqlite:///./data/research_copilot.db"
    )

    data_dir: Path = Path("./data")
    log_dir: Path = Path("./data/logs")
    chroma_dir: Path = Path("./data/chroma")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_embed_model: str = "bge-m3"

    default_chat_provider: str = "ollama"
    default_chat_model: str = "qwen3:8b"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    max_pdf_mb: int = 50
    max_pdf_pages: int = 500

    ingestion_workers: int = 2

    chunk_size: int = 1200
    chunk_overlap: int = 200

    rag_top_k: int = 12
    max_tool_calls: int = 2

    auto_compress_tokens: int = 250_000
    recent_context_tokens: int = 50_000

    @property
    def papers_dir(self) -> Path:
        return self.data_dir / "papers"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()