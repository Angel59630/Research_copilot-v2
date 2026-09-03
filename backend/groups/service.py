from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.conversations.service import (
    delete_scope_conversations,
)

from backend.groups.schemas import (
    GroupCreate,
    GroupUpdate,
)

from backend.papers.models import (
    Paper,
    PaperGroup,
    group_papers,
)


async def list_groups(
    db: AsyncSession,
) -> list[PaperGroup]:

    result = await db.execute(
        select(
            PaperGroup
        ).order_by(
            PaperGroup.name
        )
    )

    return list(
        result.scalars().all()
    )


async def create_group(
    db: AsyncSession,
    payload: GroupCreate,
) -> PaperGroup:

    group = PaperGroup(
        name=
            payload.name.strip(),

        description=
            payload.description,
    )

    db.add(
        group
    )

    await db.commit()

    await db.refresh(
        group
    )

    return group


async def update_group(
    db: AsyncSession,
    group: PaperGroup,
    payload: GroupUpdate,
) -> PaperGroup:

    values = payload.model_dump(
        exclude_unset=True
    )

    for key, value in values.items():

        if (
            key == "name"
            and value is not None
        ):
            value = value.strip()

        setattr(
            group,
            key,
            value,
        )

    await db.commit()

    await db.refresh(
        group
    )

    return group


async def delete_group(
    db: AsyncSession,
    group: PaperGroup,
) -> None:

    # 删除该分组对应会话
    # 但不删除论文
    await delete_scope_conversations(
        db,
        scope_type="group",
        scope_id=group.id,
    )

    await db.delete(
        group
    )

    await db.commit()


async def add_paper_to_group(
    db: AsyncSession,
    *,
    group_id: str,
    paper_id: str,
) -> None:

    group = await db.get(
        PaperGroup,
        group_id,
    )

    paper = await db.get(
        Paper,
        paper_id,
    )

    if group is None:
        raise LookupError(
            "分组不存在"
        )

    if paper is None:
        raise LookupError(
            "论文不存在"
        )

    exists = await db.scalar(
        select(
            group_papers.c.paper_id
        ).where(
            group_papers.c.group_id
            == group_id,

            group_papers.c.paper_id
            == paper_id,
        )
    )

    if exists is not None:
        return

    await db.execute(
        group_papers
        .insert()
        .values(
            group_id=
                group_id,

            paper_id=
                paper_id,
        )
    )

    await db.commit()


async def remove_paper_from_group(
    db: AsyncSession,
    *,
    group_id: str,
    paper_id: str,
) -> None:

    await db.execute(
        group_papers
        .delete()
        .where(
            group_papers.c.group_id
            == group_id,

            group_papers.c.paper_id
            == paper_id,
        )
    )

    await db.commit()


async def list_group_papers(
    db: AsyncSession,
    group_id: str,
) -> list[Paper]:

    group = await db.get(
        PaperGroup,
        group_id,
    )

    if group is None:
        raise LookupError(
            "分组不存在"
        )

    stmt = (
        select(
            Paper
        )
        .join(
            group_papers,

            Paper.id
            == group_papers.c.paper_id,
        )
        .where(
            group_papers.c.group_id
            == group_id
        )
        .order_by(
            Paper.created_at.desc()
        )
    )

    result = await db.execute(
        stmt
    )

    return list(
        result.scalars().all()
    )


async def list_uncategorized_papers(
    db: AsyncSession,
) -> list[Paper]:

    stmt = (
        select(
            Paper
        )
        .outerjoin(
            group_papers,

            Paper.id
            == group_papers.c.paper_id,
        )
        .where(
            group_papers.c.paper_id
            .is_(None)
        )
        .order_by(
            Paper.created_at.desc()
        )
    )

    result = await db.execute(
        stmt
    )

    return list(
        result.scalars().all()
    )