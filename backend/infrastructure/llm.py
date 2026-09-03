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
    model_config = (
        settings.get_chat_model_config(
            provider,
            model,
        )
    )

    model_url = str(
        model_config.chat_model_url
    ).rstrip("/")

    if (
        model_config
        .chat_model_provider
        == "ollama"
    ):
        return ChatOllama(
            model=(
                model_config
                .chat_model_name
            ),
            base_url=model_url,
            temperature=0,
        )

    if (
        model_config
        .chat_model_provider
        == "deepseek"
    ):
        api_key = (
            settings.resolve_api_key()
        )

        if not api_key:
            raise ValueError(
                "API_KEY 未配置，无法使用 "
                "DeepSeek 聊天模型"
            )

        return ChatOpenAI(
            model=(
                model_config
                .chat_model_name
            ),
            api_key=api_key,
            base_url=model_url,
            temperature=0,
        )

    raise ValueError(
        "不支持的聊天模型提供方"
    )