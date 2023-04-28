from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from botel.db import models


async def register_channel_and_linked_group(
    db: AsyncSession, channel_id: int, linked_group_id: int
):
    async with db.begin():
        added_linked_group = models.Chat(id=linked_group_id, type="group")
        db.add(added_linked_group)
        await db.flush()
        added_channel = models.Chat(
            id=channel_id, type="channel", linked_chat_id=added_linked_group.id
        )
        db.add(added_channel)
        await db.commit()


async def register_commentable(
    db: AsyncSession, message_id: int, channel_id: int
) -> models.Commentable:
    channel = await db.execute(
        select(models.Chat).where(
            models.Chat.id == channel_id, models.Chat.type == "channel"
        )
    )
    channel = channel.first()[0]
    if not channel:
        raise Exception("not exists")
    await db.commit()
    async with db.begin():
        added_content = models.Content(id=message_id, page_id=1)
        db.add(added_content)
        await db.flush()
        added_commentable = models.Commentable(
            group_id=channel.linked_chat_id, content_id=added_content.id
        )
        db.add(added_commentable)
        await db.commit()
        return added_commentable


async def is_commentable(db: AsyncSession, group_id: int, message_id: int) -> bool:
    result = await db.execute(
        select(models.Commentable).where(
            models.Commentable.content_id == message_id,
            models.Commentable.group_id == group_id,
        )
    )
    return bool(result.first())
