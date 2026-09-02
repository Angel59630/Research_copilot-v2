import asyncio
import re
from pathlib import Path
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "research-copilot-arxiv"
)


ARXIV_API = (
    "https://export.arxiv.org/api/query"
)


@mcp.tool()
async def search_papers(
    query: str,
    start: int = 0,
    max_results: int = 20,
) -> str:
    max_results = max(
        1,
        min(
            max_results,
            100,
        ),
    )

    params = {
        "search_query":
            f"all:{query}",
        "start":
            start,
        "max_results":
            max_results,
    }

    async with httpx.AsyncClient(
        timeout=30,
    ) as client:
        response = await client.get(
            ARXIV_API,
            params=params,
        )

        response.raise_for_status()

    return response.text


@mcp.tool()
async def resolve_paper_url(
    value: str,
) -> str:
    patterns = [
        r"arxiv\.org/abs/([^?#]+)",
        r"arxiv\.org/pdf/([^?#]+)",
        r"^(\d{4}\.\d{4,5}(?:v\d+)?)$",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            value,
        )

        if match:
            return (
                match
                .group(1)
                .removesuffix(
                    ".pdf"
                )
            )

    raise ValueError(
        "无法识别 Arxiv ID 或链接"
    )


@mcp.tool()
async def get_paper(
    paper_id: str,
) -> str:
    params = {
        "id_list":
            paper_id,
        "max_results":
            1,
    }

    async with httpx.AsyncClient(
        timeout=30,
    ) as client:
        response = await client.get(
            ARXIV_API,
            params=params,
        )

        response.raise_for_status()

    return response.text


@mcp.tool()
async def download_paper(
    paper_id: str,
    destination: str,
) -> str:
    url = (
        "https://arxiv.org/pdf/"
        f"{quote(paper_id)}"
    )

    async with httpx.AsyncClient(
        timeout=60,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            url
        )

        response.raise_for_status()

    content_type = (
        response.headers.get(
            "content-type",
            "",
        )
    )

    is_pdf = (
        "application/pdf"
        in content_type
        or response.content.startswith(
            b"%PDF"
        )
    )

    if not is_pdf:
        raise ValueError(
            "Arxiv 返回内容不是有效 PDF"
        )

    destination_path = Path(
        destination
    )

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination_path.write_bytes(
        response.content
    )

    # 简单访问间隔
    await asyncio.sleep(3)

    return str(
        destination_path
    )


if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )