from typing import Mapping

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.types import Chat, User

from botel.db import models


async def is_logged_in(db: AsyncSession, chat_id):
    user_chat = await db.execute(
        select(models.Chat).where(
            models.Chat.id == chat_id,
            models.Chat.type == "private",
            models.Chat.data == "primary",
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
    chat = models.Chat(id=chat_id, type="private", user_id=user.id, data="primary")
    db.add(chat)
    await db.commit()
    return chat, user_created


async def logout(db: AsyncSession, chat_id):
    stmt = await db.execute(
        delete(models.Chat).where(
            models.Chat.id == chat_id, models.Chat.data == "primary"
        )
    )
    await db.commit()


async def temp_in(
    db: AsyncSession, configs: Mapping, t_user: User
) -> (models.Chat, bool):
    transport = AIOHTTPTransport(url=f"http://{configs['wagtail_url']}/graphql/")
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        query = gql(
            """
            mutation ($preferredUsername: String!, $firstName: String!, $lastName: String!) {
              newTempUser(
                preferredUsername: $preferredUsername
                firstName: $firstName
                lastName: $lastName
              ) {
                user {
                  id
                }
              }
            }
            """
        )

        result = await session.execute(
            query,
            variable_values={
                "preferredUsername": t_user.username,
                "firstName": t_user.first_name or "",
                "lastName": t_user.last_name or "",
            },
        )
    user_created = False
    user_id = int(result["newTempUser"]["user"]["id"])
    user = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user.first()
    if not user:
        user = models.User(id=user_id)
        db.add(user)
        await db.flush()
        user_created = True
    else:
        user = user[0]
    chat = models.Chat(id=t_user.id, type="supergroup", user_id=user_id, data="temp")
    db.add(chat)
    await db.commit()
    return chat, user_created


async def is_temped_in(db: AsyncSession, user_id):
    user_chat = await db.execute(
        select(models.Chat).where(
            models.Chat.id == user_id,
            models.Chat.type == "supergroup",
            models.Chat.data == "temp",
        )
    )
    user_chat = user_chat.first()
    return None if not user_chat else user_chat[0]
