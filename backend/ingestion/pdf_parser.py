import json
from pathlib import Path

import pymupdf

from config import settings


class PdfValidationError(ValueError):
    pass


def parse_pdf(
    input_path: Path,
    output_jsonl: Path,
) -> int:
    try:
        document = pymupdf.open(input_path)
    except Exception as exc:
        raise PdfValidationError(
            "PDF 文件损坏或无法打开"
        ) from exc

    try:
        if document.page_count > settings.max_pdf_pages:
            raise PdfValidationError(
                f"PDF 超过最大页数 "
                f"{settings.max_pdf_pages}"
            )

        valid_text_pages = 0

        with output_jsonl.open(
            "w",
            encoding="utf-8",
        ) as fp:
            for index in range(document.page_count):
                page = document.load_page(index)

                page_number = index + 1

                text = page.get_text("text").strip()

                if text:
                    valid_text_pages += 1

                record = {
                    "page_number": page_number,
                    "text": text,
                }

                fp.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        if valid_text_pages == 0:
            output_jsonl.unlink(
                missing_ok=True
            )

            raise PdfValidationError(
                "PDF 未检测到有效文本，扫描件暂不支持"
            )

        return document.page_count

    finally:
        document.close()