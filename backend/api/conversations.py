from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from fastapi.responses import (
    StreamingResponse,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.conversations.schemas import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)

from backend.conversations.service import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
    stream_conversation_reply,
    update_conversation,
)

from backend.infrastructure.database import (
    get_session,
)


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=
        list[ConversationOut],
)
async def get_conversations(
    scope_type: str | None = None,
    scope_id: str | None = None,

    db: AsyncSession = Depends(
        get_session
    ),
):
    return await list_conversations(
        db,
        scope_type=scope_type,
        scope_id=scope_id,
    )


@router.post(
    "",
    response_model=
        ConversationOut,
)
async def post_conversation(
    payload: ConversationCreate,

    db: AsyncSession = Depends(
        get_session
    ),
):
    try:
        return (
            await
            create_conversation(
                db,
                payload,
            )
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/{conversation_id}",
    response_model=
        ConversationOut,
)
async def get_one_conversation(
    conversation_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    conversation = (
        await get_conversation(
            db,
            str(conversation_id),
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",
        )

    return conversation


@router.patch(
    "/{conversation_id}",
    response_model=ConversationOut,
)
async def patch_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,

    db: AsyncSession = Depends(
        get_session
    ),
):
    conversation = (
        await get_conversation(
            db,
            str(conversation_id),
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",
        )

    try:
        return await (
            update_conversation(
                db,
                conversation,
                payload,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{conversation_id}",
    status_code=204,
)
async def remove_conversation(
    conversation_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    conversation = (
        await get_conversation(
            db,
            str(conversation_id),
        )
    )

    if conversation is None:
        return

    await delete_conversation(
        db,
        conversation,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=
        list[MessageOut],
)
async def get_conversation_messages(
    conversation_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    conversation_id_text = str(
        conversation_id
    )

    conversation = (
        await get_conversation(
            db,
            conversation_id_text,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",
        )

    return await list_messages(
        db,
        conversation_id_text,
    )


@router.post(
    "/{conversation_id}/messages",
)
async def post_conversation_message(
    conversation_id: UUID,
    payload: MessageCreate,
    request: Request,

    db: AsyncSession = Depends(
        get_session
    ),
):
    conversation_id_text = str(
        conversation_id
    )

    conversation = (
        await get_conversation(
            db,
            conversation_id_text,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",
        )

    request_id = (
        request.state.request_id
    )

    return StreamingResponse(
        stream_conversation_reply(
            conversation_id=
                conversation_id_text,

            content=
                payload.content,

            request_id=
                request_id,
        ),

        media_type=
            "text/event-stream",

        headers={
            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no",
        },
    )