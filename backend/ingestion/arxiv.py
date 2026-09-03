from dataclasses import (
    dataclass,
)

from uuid import uuid4

import xml.etree.ElementTree as ET

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.infrastructure.arxiv_mcp import (
    arxiv_mcp,
)

from backend.infrastructure.storage import (
    pdf_path,
)

from backend.ingestion.worker import (
    ingestion_queue,
)

from backend.papers.models import (
    Paper,
)


ATOM = (
    "http://www.w3.org/"
    "2005/Atom"
)


@dataclass(
    frozen=True
)
class ArxivPaper:
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str | None
    categories:list[str]


def _text(
    element:
        ET.Element,

    path: str,
) -> str:

    value = (
        element.findtext(
            path,
            default="",
        )
    )

    return " ".join(
        value.split()
    )


def parse_arxiv_feed(
    xml_text: str,
) -> list[ArxivPaper]:

    root = ET.fromstring(
        xml_text
    )

    papers: list[ArxivPaper] = []

    for entry in root.findall(
        f"{{{ATOM}}}entry"
    ):

        id_url = _text(
            entry,
            f"{{{ATOM}}}id",
        )

        paper_id = (
            id_url.rsplit(
                "/",
                1,
            )[-1]

            if id_url
            else ""
        )

        authors = [
            _text(
                author,
                f"{{{ATOM}}}name",
            )

            for author
            in entry.findall(
                f"{{{ATOM}}}author"
            )
        ]

        categories = [
            category.attrib[
                "term"
            ]

            for category
            in entry.findall(
                f"{{{ATOM}}}category"
            )

            if category.attrib.get(
                "term"
            )
        ]

        papers.append(
            ArxivPaper(
                paper_id=
                    paper_id,

                title=
                    _text(
                        entry,
                        f"{{{ATOM}}}title",
                    ),

                authors=
                    authors,

                abstract=
                    _text(
                        entry,
                        f"{{{ATOM}}}summary",
                    ),

                published=(
                    _text(
                        entry,
                        f"{{{ATOM}}}published",
                    )
                    or None
                ),

                categories=
                    categories,
            )
        )

    return papers


async def search_arxiv(
    query: str,
    *,
    start: int = 0,
    max_results: int = 20,
) -> list[ArxivPaper]:

    xml_text = (
        await
        arxiv_mcp.call_text_tool(
            "search_papers",
            {
                "query":
                    query,

                "start":
                    start,

                "max_results":
                    max_results,
            },
        )
    )

    return parse_arxiv_feed(
        xml_text
    )


async def import_arxiv_paper(
    db: AsyncSession,
    value: str,
) -> Paper:

    # -------------------------
    # 1. URL / ID → Arxiv ID
    # -------------------------

    paper_id = (
        await
        arxiv_mcp.call_text_tool(
            "resolve_paper_url",
            {
                "value":
                    value
            },
        )
    ).strip()

    # -------------------------
    # 2. 获取 metadata
    # -------------------------

    xml_text = (
        await
        arxiv_mcp.call_text_tool(
            "get_paper",
            {
                "paper_id":
                    paper_id
            },
        )
    )

    entries = parse_arxiv_feed(
        xml_text
    )

    if not entries:
        raise LookupError(
            "未找到对应的 "
            "Arxiv 论文"
        )

    metadata = entries[0]

    # -------------------------
    # 3. 创建内部 Paper ID
    # -------------------------

    record_id = str(
        uuid4()
    )

    destination = pdf_path(
        record_id
    )

    try:

        # ---------------------
        # 4. MCP 下载 PDF
        # ---------------------

        await (
            arxiv_mcp
            .call_text_tool(
                "download_paper",
                {
                    "paper_id":
                        paper_id,

                    "destination":
                        str(
                            destination
                        ),
                },
            )
        )

        filename = (
            paper_id.replace(
                "/",
                "_",
            )
            + ".pdf"
        )

        # ---------------------
        # 5. 建立 Paper 记录
        # ---------------------

        paper = Paper(
            id=
                record_id,

            title=(
                metadata.title
                or paper_id
            ),

            authors=(
                ", ".join(
                    metadata.authors
                )
                or None
            ),

            abstract=(
                metadata.abstract
                or None
            ),

            source=
                "arxiv",

            source_id=
                paper_id,

            filename=
                filename,

            status=
                "queued",

            file_size=
                destination
                .stat()
                .st_size,
        )

        db.add(
            paper
        )

        await db.commit()

        await db.refresh(
            paper
        )

    except Exception:

        destination.unlink(
            missing_ok=True
        )

        raise

    # -------------------------
    # 6. 复用已有 PDF pipeline
    # -------------------------

    await ingestion_queue.enqueue(
        paper.id
    )

    return paper