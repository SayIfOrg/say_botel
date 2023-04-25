import asyncio
import os
import sys

from dotenv import load_dotenv
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

    bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])

    bot.add_custom_filter(StateFilter(bot))

    if proxy_url := os.environ.get("PROXY_URL"):
        from telebot import asyncio_helper

        asyncio_helper.proxy = proxy_url

    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        await botel.grpc_gate.server.serve(db_initializer=get_session, bot=bot)
    elif sys.argv[1] == "poll":
        # Private
        bot.message_handler(commands=["register_me"])(
            handlers.register_for_blog(db_initializer=get_session)
        )
        bot.message_handler(commands=["m"])(handlers.menu)
        bot.callback_query_handler(
            func=lambda x: x.data == QUERY_DATA.REGISTER_CHANEL.value
        )(handlers.add_to_a_channel_state)
        bot.callback_query_handler(
            func=lambda x: x.data == QUERY_DATA.CANCEL.value,
            state=STATES.REGISTERING_CHANEL.value,
        )(handlers.add_to_a_channel_state)
        bot.message_handler(state=STATES.REGISTERING_CHANEL.value)(
            handlers.add_to_a_channel
        )
        # Chat
        bot.my_chat_member_handler(func=lambda x: True)(handlers.echo_bot_chat_events)
        bot.channel_post_handler(func=lambda x: True)(handlers.channel_post)
        # Group
        bot.message_handler(
            func=lambda x: x.reply_to_message, chat_types=["supergroup"]
        )(handlers.group_replies)
        bot.message_handler(chat_types=["supergroup"])(handlers.group_messages)

        # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
        bot.message_handler(func=lambda message: True)(handlers.echo_message)

        await bot.polling(request_timeout=1000)
    elif sys.argv[1] == "dbpush":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(amain())
