from langchain_ollama import (
    ChatOllama,
)
from langchain_openai import (
    ChatOpenAI,
)

from config import settings


def create_chat_model(
    provider: str,
    model: str,
):
    if provider == "ollama":
        return ChatOllama(
            model=model,
            base_url=(
                settings.ollama_base_url
            ),
            temperature=0,
        )

    if provider == "deepseek":
        if not (
            settings.deepseek_api_key
        ):
            raise RuntimeError(
                "DEEPSEEK_API_KEY "
                "未配置"
            )

        return ChatOpenAI(
            model=model,
            api_key=(
                settings.deepseek_api_key
            ),
            base_url=(
                settings.deepseek_base_url
            ),
            temperature=0,
        )

    raise ValueError(
        "Unsupported provider: "
        f"{provider}"
    )