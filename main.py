import asyncio
import os
import sys

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

import botel.grpc_gate.server


def configure():
    load_dotenv(dotenv_path=".env", override=True)


async def amain():
    configure()
    from botel import handlers
    from botel.db import models
    from botel.db.engine import get_session, engine

    bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])

    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        await botel.grpc_gate.server.serve(db_initializer=get_session, bot=bot)
    elif sys.argv[1] == "poll":
        bot.message_handler(commands=["register_me"])(
            handlers.register_for_blog(db_initializer=get_session)
        )

        # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
        bot.message_handler(func=lambda message: True)(handlers.echo_message)

        await bot.polling(request_timeout=1000)
    elif sys.argv[1] == "dbpush":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(amain())
