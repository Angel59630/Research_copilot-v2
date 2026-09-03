from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.groups.schemas import (
    GroupCreate,
    GroupOut,
    GroupUpdate,
)

from backend.groups.service import (
    add_paper_to_group,
    create_group,
    delete_group,
    list_group_papers,
    list_groups,
    list_uncategorized_papers,
    remove_paper_from_group,
    update_group,
)

from backend.infrastructure.database import (
    get_session,
)

from backend.papers.models import (
    PaperGroup,
)

from backend.papers.schemas import (
    PaperOut,
)


router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@router.get(
    "",
    response_model=
        list[GroupOut],
)
async def get_groups(
    db: AsyncSession = Depends(
        get_session
    ),
):
    return await list_groups(
        db
    )


@router.post(
    "",
    response_model=
        GroupOut,
)
async def post_group(
    payload: GroupCreate,

    db: AsyncSession = Depends(
        get_session
    ),
):
    return await create_group(
        db,
        payload,
    )


@router.get(
    "/uncategorized/papers",
    response_model=
        list[PaperOut],
)
async def get_uncategorized(
    db: AsyncSession = Depends(
        get_session
    ),
):
    return (
        await
        list_uncategorized_papers(
            db
        )
    )


@router.patch(
    "/{group_id}",
    response_model=
        GroupOut,
)
async def patch_group(
    group_id: UUID,
    payload: GroupUpdate,

    db: AsyncSession = Depends(
        get_session
    ),
):
    group = await db.get(
        PaperGroup,
        str(group_id),
    )

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="分组不存在",
        )

    return await update_group(
        db,
        group,
        payload,
    )


@router.delete(
    "/{group_id}",
    status_code=204,
)
async def remove_group(
    group_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    group = await db.get(
        PaperGroup,
        str(group_id),
    )

    if group is None:
        return

    await delete_group(
        db,
        group,
    )


@router.get(
    "/{group_id}/papers",
    response_model=
        list[PaperOut],
)
async def get_group_papers(
    group_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    try:
        return (
            await list_group_papers(
                db,
                str(group_id),
            )
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.put(
    "/{group_id}/papers/{paper_id}",
    status_code=204,
)
async def put_group_paper(
    group_id: UUID,
    paper_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    try:
        await add_paper_to_group(
            db,
            group_id=
                str(group_id),

            paper_id=
                str(paper_id),
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{group_id}/papers/{paper_id}",
    status_code=204,
)
async def delete_group_paper(
    group_id: UUID,
    paper_id: UUID,

    db: AsyncSession = Depends(
        get_session
    ),
):
    await remove_paper_from_group(
        db,
        group_id=
            str(group_id),

        paper_id=
            str(paper_id),
    )