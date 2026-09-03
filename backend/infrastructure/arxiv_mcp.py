import asyncio
import json
import sys

from contextlib import (
    AsyncExitStack,
)

from pathlib import Path

from mcp import (
    Client,
    StdioServerParameters,
    stdio_client,
)

from mcp.types import (
    TextContent,
)

from config import settings


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


ARXIV_SERVER = (
    PROJECT_ROOT
    / "mcp"
    / "arxiv"
    / "server.py"
)


MCP_LOG_PATH = (
    settings.log_dir
    / "arxiv_mcp.log"
)


class ArxivMCPClient:

    def __init__(
        self,
    ) -> None:
        self._stack: (
            AsyncExitStack | None
        ) = None

        self._client: (
            Client | None
        ) = None

        self._lock = (
            asyncio.Lock()
        )


    @property
    def started(
        self,
    ) -> bool:
        return (
            self._client
            is not None
        )


    async def start(
        self,
    ) -> None:

        async with self._lock:

            if (
                self._client
                is not None
            ):
                return

            settings.log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            log_file = open(
                MCP_LOG_PATH,
                "a",
                encoding="utf-8",
                buffering=1,
            )

            stack = (
                AsyncExitStack()
            )

            stack.callback(
                log_file.close
            )

            params = (
                StdioServerParameters(
                    command=
                        sys.executable,

                    args=[
                        str(
                            ARXIV_SERVER
                        )
                    ],

                    cwd=
                        str(
                            PROJECT_ROOT
                        ),
                )
            )

            # 使用显式 stdio transport，
            # 这样可以把 MCP Server 的 stderr
            # 写入单独的日志文件
            transport = stdio_client(
                params,
                errlog=log_file,
            )

            client = Client(
                transport,

                # MCP 2.x 默认推荐 auto：
                # 优先使用 2026-07-28，
                # 必要时兼容旧协议
                mode="auto",
            )

            try:
                await (
                    stack
                    .enter_async_context(
                        client
                    )
                )

            except BaseException:
                await stack.aclose()
                raise

            self._stack = stack
            self._client = client


    async def stop(
        self,
    ) -> None:

        async with self._lock:

            stack = (
                self._stack
            )

            self._stack = None
            self._client = None

            if stack is not None:
                await stack.aclose()


    async def call_text_tool(
        self,
        name: str,
        arguments: dict,
    ) -> str:

        if (
            self._client
            is None
        ):
            await self.start()

        client = (
            self._client
        )

        if client is None:
            raise RuntimeError(
                "Arxiv MCP Client "
                "启动失败"
            )

        result = (
            await client.call_tool(
                name,
                arguments,
            )
        )

        text_parts = [
            block.text

            for block
            in result.content

            if isinstance(
                block,
                TextContent,
            )
        ]

        text = "\n".join(
            text_parts
        ).strip()

        # MCP 2.x：
        # CallToolResult 使用 is_error，
        # 不是旧式 isError
        if result.is_error:
            raise RuntimeError(
                text
                or
                (
                    "Arxiv MCP 工具调用失败: "
                    f"{name}"
                )
            )

        if text:
            return text

        # 正常情况下我们自己的 Arxiv MCP
        # 已设置 structured_output=False，
        # 因此会从 content 返回文本。
        #
        # 这里保留 structured_content fallback，
        # 方便未来某个工具改为结构化结果。
        if (
            result.structured_content
            is not None
        ):

            structured = (
                result
                .structured_content
            )

            if (
                isinstance(
                    structured,
                    dict,
                )
                and
                set(
                    structured.keys()
                ) == {"result"}
                and
                isinstance(
                    structured.get(
                        "result"
                    ),
                    str,
                )
            ):
                return structured[
                    "result"
                ]

            return json.dumps(
                structured,
                ensure_ascii=False,
            )

        raise RuntimeError(
            "Arxiv MCP 工具 "
            f"{name} 未返回可读取内容"
        )


arxiv_mcp = (
    ArxivMCPClient()
)