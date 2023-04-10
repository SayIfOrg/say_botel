from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import telebot.types

from db import models


async def publish_record(db: AsyncSession, page_id, message_id):
    async with db.begin():
        db.add_all(
            [
                models.PublishHistory(page_id=page_id, message_id=message_id),
            ]
        )


async def get_page_records(db: AsyncSession, page_id):
    result = await db.execute(
        select(models.PublishHistory).filter_by(page_id=page_id)
    )

    return result.scalars()


async def get_project_instances(db: AsyncSession, project_id):
    result = await db.execute(
        select(models.BlogRegistered).filter_by(project_oid=project_id)
    )

    return result.scalars()


async def get_instance(db: AsyncSession, id):
    result = await db.get(models.BlogRegistered, id)

    return result


async def register_instance(db: AsyncSession, project_oid, created_by_oid, chat: telebot.types.Chat):
    created_by_chat = get_or_create_chat(db, type=chat.type, data=str(chat))
    the_chat = get_or_create_chat(db, type=chat.type, data=str(chat))
    new_instance = models.BlogRegistered(
        project_oid=project_oid,
        created_by_oid=created_by_oid,
        created_by_chat=created_by_chat.id,
        chat_id=the_chat.id,
    )
    db.add(new_instance)
    await db.flush()
    return new_instance


async def get_or_create_chat(db: AsyncSession, type: str, data: str):
    result = await db.execute(
        select(models.Chat).filter_by(type=type, data=data)
    )
    result = result.scalars()
    if result:
        return result[0]
    result = models.Chat(type=type, data=data)
    db.add(result)
    await db.flush()
    return result
