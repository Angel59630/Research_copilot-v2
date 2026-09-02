from __future__ import annotations

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from backend.infrastructure.models import (
    Base,
    TimestampMixin,
    UUIDMixin,
)


class Conversation(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(
        String(300),
        default="新会话",
    )

    scope_type: Mapped[str] = mapped_column(
        String(16),
    )

    scope_id: Mapped[str] = mapped_column(
        String(36),
    )

    model_provider: Mapped[str] = (
        mapped_column(
            String(50),
        )
    )

    model_name: Mapped[str] = (
        mapped_column(
            String(200),
        )
    )

    supports_tool_calling: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        default=True,
    )

    compressed_summary: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    compressed_until_message: Mapped[
        int
    ] = mapped_column(
        Integer,
        default=0,
    )

    messages: Mapped[
        list["Message"]
    ] = relationship(
        back_populates=(
            "conversation"
        ),
        cascade=(
            "all, delete-orphan"
        ),
        order_by=(
            "Message.sequence"
        ),
    )


class Message(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __tablename__ = "messages"

    conversation_id: Mapped[
        str
    ] = mapped_column(
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
    )

    conversation: Mapped[
        Conversation
    ] = relationship(
        back_populates="messages",
    )

    citations: Mapped[
        list["Citation"]
    ] = relationship(
        back_populates="message",
        cascade=(
            "all, delete-orphan"
        ),
    )


class Citation(
    Base,
    UUIDMixin,
):
    __tablename__ = "citations"

    message_id: Mapped[
        str
    ] = mapped_column(
        ForeignKey(
            "messages.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    source_number: Mapped[
        int
    ] = mapped_column(
        Integer,
    )

    paper_id: Mapped[str] = mapped_column(
        String(36),
    )

    paper_title: Mapped[
        str
    ] = mapped_column(
        String(500),
    )

    page_number: Mapped[
        int
    ] = mapped_column(
        Integer,
    )

    chunk_id: Mapped[str] = mapped_column(
        String(100),
    )

    message: Mapped[
        Message
    ] = relationship(
        back_populates="citations",
    )