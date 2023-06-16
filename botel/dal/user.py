from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from botel.db import models


async def is_logged_in(db: AsyncSession, chat_id):
    user_chat = await db.execute(
        select(models.Chat).where(
            models.Chat.id == chat_id, models.Chat.type == "private"
        )
    )
    user_chat = user_chat.first()
    return None if not user_chat else user_chat[0]


async def login(db: AsyncSession, chat_id, user_id) -> (models.Chat, bool):
    user_created = False
    user = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user.first()
    if not user:
        user = models.User(id=user_id)
        db.add(user)
        await db.flush()
        user_created = True
    else:
        user = user[0]
    chat = models.Chat(id=chat_id, type="private", user_id=user.id)
    db.add(chat)
    await db.commit()
    return chat, user_created


async def logout(db: AsyncSession, chat_id):
    stmt = await db.execute(delete(models.Chat).where(models.Chat.id == chat_id))
    await db.commit()
