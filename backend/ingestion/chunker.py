from dataclasses import dataclass


@dataclass(frozen=True)
class PaperChunk:
    chunk_id: str
    paper_id: str
    page_number: int
    chunk_index: int
    text: str


def chunk_page(
    *,
    paper_id: str,
    page_number: int,
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[PaperChunk]:
    if not text.strip():
        return []

    chunks: list[PaperChunk] = []

    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id = (
                f"{paper_id}:"
                f"{page_number}:"
                f"{chunk_index}"
            )

            chunks.append(
                PaperChunk(
                    chunk_id=chunk_id,
                    paper_id=paper_id,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                )
            )

        if end >= len(text):
            break

        start = max(
            0,
            end - overlap,
        )

        chunk_index += 1

    return chunks