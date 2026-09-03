import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


ENV_REFERENCE_PATTERN = re.compile(
    r"^\{([A-Za-z_][A-Za-z0-9_]*)\}$"
)


class ChatModelConfig(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    chat_model_provider: Literal[
        "deepseek",
        "ollama",
    ]
    chat_model_url: AnyHttpUrl
    chat_model_name: str

    @field_validator(
        "chat_model_name"
    )
    @classmethod
    def validate_model_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "聊天模型名称不能为空"
            )

        return value


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
        "sqlite+aiosqlite:///"
        "./data/research_copilot.db"
    )

    data_dir: Path = Path("./data")
    log_dir: Path = Path(
        "./data/logs"
    )
    chroma_dir: Path = Path(
        "./data/chroma"
    )

    log_level: str = "INFO"
    log_max_bytes: int = (
        10 * 1024 * 1024
    )
    log_backup_count: int = 5

    # Embedding 使用的 Ollama 配置
    ollama_base_url: str = (
        "http://100.73.210.42:11434"
    )
    ollama_embed_model: str = "bge-m3"

    # 统一聊天模型密钥
    api_key: SecretStr | None = None

    # 第一项是默认聊天模型
    chat_models: tuple[
        ChatModelConfig,
        ...,
    ] = (
        ChatModelConfig(
            chat_model_provider=(
                "deepseek"
            ),
            chat_model_url=(
                "https://api.deepseek.com"
            ),
            chat_model_name=(
                "deepseek-chat"
            ),
        ),
        ChatModelConfig(
            chat_model_provider=(
                "ollama"
            ),
            chat_model_url=(
                "http://100.73.210.42:11434"
            ),
            chat_model_name="qwen3:8b",
        ),
    )

    max_pdf_mb: int = 50
    max_pdf_pages: int = 500

    ingestion_workers: int = 2

    chunk_size: int = 1200
    chunk_overlap: int = 200

    rag_top_k: int = 12
    max_tool_calls: int = 2

    auto_compress_tokens: int = (
        250_000
    )
    recent_context_tokens: int = (
        50_000
    )

    @model_validator(mode="after")
    def validate_chat_models(
        self,
    ):
        if not self.chat_models:
            raise ValueError(
                "至少需要配置一个聊天模型"
            )

        identities = [
            (
                item.chat_model_provider,
                item.chat_model_name,
            )
            for item in self.chat_models
        ]

        if len(identities) != len(
            set(identities)
        ):
            raise ValueError(
                "聊天模型配置存在重复项"
            )

        return self

    @property
    def default_chat_model_config(
        self,
    ) -> ChatModelConfig:
        return self.chat_models[0]

    def get_chat_model_config(
        self,
        provider: str,
        model_name: str,
    ) -> ChatModelConfig:
        provider = provider.strip()
        model_name = model_name.strip()

        for item in self.chat_models:
            if (
                item.chat_model_provider
                == provider
                and item.chat_model_name
                == model_name
            ):
                return item

        raise ValueError(
            "指定的聊天模型不可用"
        )

    def resolve_api_key(
        self,
    ) -> str | None:
        if self.api_key is None:
            return None

        raw_value = (
            self.api_key
            .get_secret_value()
            .strip()
        )

        if not raw_value:
            return None

        match = (
            ENV_REFERENCE_PATTERN
            .fullmatch(raw_value)
        )

        if match is None:
            return raw_value

        environment_name = (
            match.group(1)
        )

        resolved = os.environ.get(
            environment_name
        )

        if not resolved:
            raise ValueError(
                "API_KEY 引用的 Windows "
                f"环境变量 {environment_name} "
                "未配置"
            )

        return resolved

    @property
    def papers_dir(self) -> Path:
        return self.data_dir / "papers"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()