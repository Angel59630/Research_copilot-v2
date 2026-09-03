from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.orm import (
    selectinload,
)

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

from backend.conversations.models import (
    Conversation,
    Message,
)
from backend.conversations.schemas import (
    ConversationCreate,
    ConversationUpdate,
)
from backend.infrastructure.database import (
    SessionFactory,
)
from backend.infrastructure.llm import (
    create_chat_model,
)
from backend.papers.models import (
    Paper,
    PaperGroup,
    group_papers,
)
from backend.rag.graph import (
    build_rag_graph,
)
from backend.rag.streaming import (
    sse_event,
    stream_graph,
)
from backend.rag.types import (
    RagRuntimeContext,
    ScopePaper,
)
from config import settings


async def validate_scope(
    db: AsyncSession,
    scope_type: str,
    scope_id: str,
) -> None:

    if scope_type == "paper":
        paper = await db.get(
            Paper,
            scope_id,
        )

        if paper is None:
            raise LookupError(
                "论文不存在"
            )

        return

    if scope_type == "group":
        group = await db.get(
            PaperGroup,
            scope_id,
        )

        if group is None:
            raise LookupError(
                "分组不存在"
            )

        return

    raise ValueError(
        "不支持的会话范围"
    )


async def resolve_rag_scope(
    db: AsyncSession,
    conversation: Conversation,
) -> tuple[
    str,
    tuple[ScopePaper, ...],
]:
    """解析本轮可读范围名称和可检索论文目录。"""

    if (
        conversation.scope_type
        == "paper"
    ):
        paper = await db.get(
            Paper,
            conversation.scope_id,
        )

        if paper is None:
            raise LookupError(
                "论文不存在"
            )

        if paper.status != "ready":
            return (
                paper.title,
                (),
            )

        return (
            paper.title,
            (
                ScopePaper(
                    ref="P1",
                    paper_id=paper.id,
                    title=paper.title,
                    authors=paper.authors,
                ),
            ),
        )

    if (
        conversation.scope_type
        != "group"
    ):
        raise ValueError(
            "不支持的会话范围"
        )

    group = await db.get(
        PaperGroup,
        conversation.scope_id,
    )

    if group is None:
        raise LookupError(
            "分组不存在"
        )

    stmt = (
        select(Paper)
        .join(
            group_papers,
            Paper.id
            == group_papers.c.paper_id,
        )
        .where(
            group_papers.c.group_id
            == conversation.scope_id,

            Paper.status
            == "ready",
        )
        .order_by(
            func.lower(
                Paper.title
            ),
            Paper.id,
        )
    )

    result = await db.execute(
        stmt
    )

    papers = list(
        result.scalars().all()
    )

    available_papers = tuple(
        ScopePaper(
            ref=f"P{index}",
            paper_id=paper.id,
            title=paper.title,
            authors=paper.authors,
        )
        for index, paper in enumerate(
            papers,
            start=1,
        )
    )

    return (
        group.name,
        available_papers,
    )


async def create_conversation(
    db: AsyncSession,
    payload: ConversationCreate,
) -> Conversation:
    await validate_scope(
        db,
        payload.scope_type,
        payload.scope_id,
    )

    if payload.model_provider is None:
        model_config = (
            settings
            .default_chat_model_config
        )
    else:
        model_config = (
            settings.get_chat_model_config(
                payload.model_provider,
                payload.model_name or "",
            )
        )

    conversation = Conversation(
        title=payload.title.strip(),

        scope_type=(
            payload.scope_type
        ),

        scope_id=payload.scope_id,

        model_provider=(
            model_config
            .chat_model_provider
        ),

        model_name=(
            model_config
            .chat_model_name
        ),

        supports_tool_calling=True,
    )

    db.add(conversation)

    await db.commit()
    await db.refresh(conversation)

    return conversation


async def list_conversations(
    db: AsyncSession,
    *,
    scope_type: str | None = None,
    scope_id: str | None = None,
) -> list[Conversation]:

    stmt = select(
        Conversation
    )

    if scope_type:
        stmt = stmt.where(
            Conversation.scope_type
            == scope_type
        )

    if scope_id:
        stmt = stmt.where(
            Conversation.scope_id
            == scope_id
        )

    stmt = stmt.order_by(
        Conversation.updated_at.desc()
    )

    result = await db.execute(
        stmt
    )

    return list(
        result.scalars().all()
    )


async def get_conversation(
    db: AsyncSession,
    conversation_id: str,
) -> Conversation | None:

    return await db.get(
        Conversation,
        conversation_id,
    )


async def update_conversation(
    db: AsyncSession,
    conversation: Conversation,
    payload: ConversationUpdate,
) -> Conversation:
    values = payload.model_dump(
        exclude_unset=True
    )

    model_fields = {
        "model_provider",
        "model_name",
    }

    if (
        model_fields
        & payload.model_fields_set
    ):
        model_config = (
            settings.get_chat_model_config(
                payload.model_provider
                or "",
                payload.model_name
                or "",
            )
        )

        values["model_provider"] = (
            model_config
            .chat_model_provider
        )

        values["model_name"] = (
            model_config
            .chat_model_name
        )

    for key, value in values.items():
        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

        setattr(
            conversation,
            key,
            value,
        )

    await db.commit()
    await db.refresh(conversation)

    return conversation


async def delete_conversation(
    db: AsyncSession,
    conversation: Conversation,
) -> None:

    await db.delete(
        conversation
    )

    await db.commit()


async def delete_scope_conversations(
    db: AsyncSession,
    *,
    scope_type: str,
    scope_id: str,
) -> None:

    await db.execute(
        delete(
            Conversation
        ).where(
            Conversation.scope_type
            == scope_type,

            Conversation.scope_id
            == scope_id,
        )
    )


async def list_messages(
    db: AsyncSession,
    conversation_id: str,
) -> list[Message]:

    stmt = (
        select(
            Message
        )
        .options(
            selectinload(
                Message.citations
            )
        )
        .where(
            Message.conversation_id
            == conversation_id
        )
        .order_by(
            Message.sequence
        )
    )

    result = await db.execute(
        stmt
    )

    return list(
        result.scalars().all()
    )


async def _next_sequence(
    db: AsyncSession,
    conversation_id: str,
) -> int:

    current = await db.scalar(
        select(
            func.max(
                Message.sequence
            )
        ).where(
            Message.conversation_id
            == conversation_id
        )
    )

    return int(
        current or 0
    ) + 1


def _to_langchain_messages(
    messages: list[Message],
):
    result = []

    for message in messages:

        if message.role == "user":
            result.append(
                HumanMessage(
                    content=
                        message.content
                )
            )

        elif (
            message.role
            == "assistant"
        ):
            result.append(
                AIMessage(
                    content=
                        message.content
                )
            )

    return result


async def stream_conversation_reply(
    *,
    conversation_id: str,
    content: str,
    request_id: str,
):

    # -------------------------
    # 1. 保存用户消息
    # -------------------------

    async with (
        SessionFactory()
        as db
    ):
        conversation = await db.get(
            Conversation,
            conversation_id,
        )

        if conversation is None:
            raise LookupError(
                "会话不存在"
            )

        user_message = Message(
            conversation_id=
                conversation.id,

            role="user",

            content=content,

            sequence=
                await _next_sequence(
                    db,
                    conversation.id,
                ),
        )

        db.add(
            user_message
        )

        await db.commit()

        # 当前完整历史
        history = await list_messages(
            db,
            conversation.id,
        )

        # 每轮重新读取范围名称和
        # 当前所有可检索论文
        (
            scope_name,
            available_papers,
        ) = await resolve_rag_scope(
            db,
            conversation,
        )

        allowed_paper_ids = tuple(
            paper.paper_id
            for paper
            in available_papers
        )

        model_provider = (
            conversation.model_provider
        )

        model_name = (
            conversation.model_name
        )

        scope_type = (
            conversation.scope_type
        )

        scope_id = (
            conversation.scope_id
        )

    context = RagRuntimeContext(
        conversation_id=
            conversation_id,

        scope_type=
            scope_type,

        scope_id=
            scope_id,

        scope_name=
            scope_name,

        available_papers=
            available_papers,

        allowed_paper_ids=
            allowed_paper_ids,

        request_id=
            request_id,

        top_k=
            settings.rag_top_k,
    )

    # -------------------------
    # 2. 创建 LLM + LangGraph
    # -------------------------

    try:
        model = create_chat_model(
            model_provider,
            model_name,
        )

        graph = build_rag_graph(
            model,
            context=context,
        )

    except ValueError as exc:
        yield sse_event(
            "failure",
            {
                "message":
                    str(exc),

                "request_id":
                    request_id,
            },
        )

        return

    answer_parts: list[str] = []

    # -------------------------
    # 3. 收集流式输出
    # -------------------------

    def capture_delta(
        text: str,
    ) -> None:
        answer_parts.append(
            text
        )

    # -------------------------
    # 4. 只有生成成功
    #    才保存 assistant
    # -------------------------

    async def persist_answer():
        answer = "".join(
            answer_parts
        ).strip()

        if not answer:
            return

        async with (
            SessionFactory()
            as db
        ):
            assistant_message = (
                Message(
                    conversation_id=
                        conversation_id,

                    role="assistant",

                    content=
                        answer,

                    sequence=
                        await
                        _next_sequence(
                            db,
                            conversation_id,
                        ),
                )
            )

            db.add(
                assistant_message
            )

            await db.commit()

    # -------------------------
    # 5. SSE
    # -------------------------

    async for chunk in stream_graph(
        graph=graph,

        input_state={
            "messages":
                _to_langchain_messages(
                    history
                ),

            "tool_call_count": 0,
        },

        context=context,

        on_delta=
            capture_delta,

        on_done=
            persist_answer,
    ):
        yield chunk