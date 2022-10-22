from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import telebot.types

from db import models
from db.operations.engin import get_session


async def publish_record(page_id, message_id):
    async with get_session() as session:
        async with session.begin():
            session.add_all(
                [
                    models.PublishHistory(page_id=page_id, message_id=message_id),
                ]
            )


async def get_page_records(page_id):
    async with get_session() as session:
        result = await session.execute(
            select(models.PublishHistory).filter_by(page_id=page_id)
        )

        return result.scalars()


async def get_project_instances(project_id):
    async with get_session() as session:
        result = await session.execute(
            select(models.BlogRegistered).filter_by(project_oid=project_id)
        )

        return result.scalars()


async def get_instance(id):
    async with get_session() as session:
        result = await session.get(models.BlogRegistered, id)

        return result


async def register_instance(project_oid, created_by_oid, chat: telebot.types.Chat):
    async with get_session() as session:
        created_by_chat = get_or_create_chat(type=chat.type, data=str(chat))
        the_chat = get_or_create_chat(type=chat.type, data=str(chat))
        new_instance = models.BlogRegistered(
            project_oid=project_oid,
            created_by_oid=created_by_oid,
            created_by_chat=created_by_chat.id,
            chat_id=the_chat.id,
        )
        session.add(new_instance)
        await session.flush()
        return new_instance


async def get_or_create_chat(type: str, data: str):
    async with get_session() as session:
        result = await session.execute(
            select(models.Chat).filter_by(type=type, data=data)
        )
        result = result.scalars()
        if result:
            return result[0]
        result = models.Chat(type=type, data=data)
        session.add(result)
        await session.flush()
        return result
