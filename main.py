import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from telebot.asyncio_filters import StateFilter
from telebot.async_telebot import AsyncTeleBot

import botel.grpc_gate.server
from botel.handlers import STATES, QUERY_DATA


def configure():
    load_dotenv(dotenv_path=".env", override=True)


async def amain():
    configure()
    from botel import handlers
    from botel.db import models
    from botel.db.engine import get_session, engine

    if proxy_url := os.environ.get("PROXY_URL"):
        from telebot import asyncio_helper

        asyncio_helper.proxy = proxy_url

    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        await botel.grpc_gate.server.serve(db_initializer=get_session)
    elif sys.argv[1] == "poll":
        # multibots functionality via poll, Not ideal but possible
        async with get_session() as db:
            result = await db.execute(select(models.Bot))
            bots = result.scalars()
        poll_tasks: list[asyncio.Task] = []
        for bot in bots:
            telebot = AsyncTeleBot(bot.api_token)
            telebot.add_custom_filter(StateFilter(telebot))
            # Private
            telebot.message_handler(commands=["register_me"])(
                handlers.register_for_blog(db_initializer=get_session)
            )
            telebot.message_handler(commands=["m"])(handlers.menu)
            telebot.callback_query_handler(
                func=lambda x: x.data == QUERY_DATA.REGISTER_CHANEL.value
            )(handlers.add_to_a_channel_state)
            telebot.callback_query_handler(
                func=lambda x: x.data == QUERY_DATA.CANCEL.value,
                state=STATES.REGISTERING_CHANEL.value,
            )(handlers.add_to_a_channel_state)
            telebot.message_handler(state=STATES.REGISTERING_CHANEL.value)(
                handlers.add_to_a_channel
            )
            # Chat
            telebot.my_chat_member_handler(func=lambda x: True)(
                handlers.echo_bot_chat_events
            )
            telebot.channel_post_handler(func=lambda x: True)(handlers.channel_post)
            # Group
            telebot.message_handler(
                func=lambda x: x.reply_to_message, chat_types=["supergroup"]
            )(handlers.group_replies)
            telebot.message_handler(chat_types=["supergroup"])(handlers.group_messages)

            # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
            telebot.message_handler(func=lambda message: True)(handlers.echo_message)

            poll_task = asyncio.create_task(telebot.polling(request_timeout=1000))
            poll_tasks.append(poll_task)
        await asyncio.gather(*poll_tasks)
    elif sys.argv[1] == "dbpush":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(amain())
