import asyncio
import re
from pathlib import Path
from urllib.parse import quote

import httpx

from mcp.server import MCPServer


mcp = MCPServer(
    "research-copilot-arxiv"
)


ARXIV_API = (
    "https://export.arxiv.org/api/query"
)


@mcp.tool(structured_output=False)
async def search_papers(
    query: str,
    start: int = 0,
    max_results: int = 20,
) -> str:
    """
    Search papers from the Arxiv API.

    Returns the original Atom XML response.
    """

    query = query.strip()

    if not query:
        raise ValueError(
            "搜索关键词不能为空"
        )

    start = max(
        0,
        start,
    )

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
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            ARXIV_API,
            params=params,
        )

        response.raise_for_status()

    return response.text


@mcp.tool(structured_output=False)
async def resolve_paper_url(
    value: str,
) -> str:
    """
    Resolve an Arxiv URL or Arxiv ID
    into a normalized paper ID.
    """

    value = value.strip()

    if not value:
        raise ValueError(
            "Arxiv ID 或链接不能为空"
        )

    patterns = [
        r"arxiv\.org/abs/([^?#]+)",
        r"arxiv\.org/pdf/([^?#]+)",

        # 新式 Arxiv ID
        r"^(\d{4}\.\d{4,5}(?:v\d+)?)$",

        # 旧式 Arxiv ID，例如：
        # hep-th/9901001
        r"^([a-zA-Z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)$",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            value,
            flags=re.IGNORECASE,
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


@mcp.tool(structured_output=False)
async def get_paper(
    paper_id: str,
) -> str:
    """
    Get metadata for one Arxiv paper.

    Returns the original Atom XML response.
    """

    paper_id = paper_id.strip()

    if not paper_id:
        raise ValueError(
            "Arxiv ID 不能为空"
        )

    params = {
        "id_list":
            paper_id,
        "max_results":
            1,
    }

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            ARXIV_API,
            params=params,
        )

        response.raise_for_status()

    return response.text


@mcp.tool(structured_output=False)
async def download_paper(
    paper_id: str,
    destination: str,
) -> str:
    """
    Download an Arxiv PDF
    to the specified local path.
    """

    paper_id = paper_id.strip()

    if not paper_id:
        raise ValueError(
            "Arxiv ID 不能为空"
        )

    destination = destination.strip()

    if not destination:
        raise ValueError(
            "PDF 保存路径不能为空"
        )

    url = (
        "https://arxiv.org/pdf/"
        f"{quote(paper_id)}"
    )

    async with httpx.AsyncClient(
        timeout=60.0,
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
        in content_type.lower()
        or
        response.content.startswith(
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

    # 避免对 Arxiv 产生过于频繁的请求
    await asyncio.sleep(3)

    return str(
        destination_path
    )


if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )