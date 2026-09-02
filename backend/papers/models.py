from __future__ import annotations

from sqlalchemy import ForeignKey, String, Table, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.infrastructure.models import Base, TimestampMixin, UUIDMixin


paper_tags = Table(
    "paper_tags",
    Base.metadata,
    Column("paper_id", ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


group_papers = Table(
    "group_papers",
    Base.metadata,
    Column("group_id", ForeignKey("paper_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("paper_id", ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
)


class Paper(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "papers"

    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)

    source: Mapped[str] = mapped_column(String(32), default="local")
    source_id: Mapped[str | None] = mapped_column(String(255))

    filename: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)

    page_count: Mapped[int | None]
    file_size: Mapped[int | None]

    tags: Mapped[list[Tag]] = relationship(
        secondary=paper_tags,
        back_populates="papers",
    )
    groups: Mapped[list[PaperGroup]] = relationship(
        secondary=group_papers,
        back_populates="papers",
    )


class Tag(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True)

    papers: Mapped[list[Paper]] = relationship(
        secondary=paper_tags,
        back_populates="tags",
    )


class PaperGroup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "paper_groups"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    papers: Mapped[list[Paper]] = relationship(
        secondary=group_papers,
        back_populates="groups",
    )