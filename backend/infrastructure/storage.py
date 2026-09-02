import shutil
from pathlib import Path

from config import settings


def paper_dir(paper_id: str) -> Path:
    path = settings.papers_dir / paper_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def pdf_path(paper_id: str) -> Path:
    return paper_dir(paper_id) / "paper.pdf"


def pages_path(paper_id: str) -> Path:
    return paper_dir(paper_id) / "pages.jsonl"


def delete_paper_files(paper_id: str) -> None:
    path = settings.papers_dir / paper_id
    if path.exists():
        shutil.rmtree(path)