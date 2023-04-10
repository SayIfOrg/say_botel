import asyncio
import os
import sys

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

import grpc_gate.server


def configure():
    load_dotenv(dotenv_path=".env", override=True)


if __name__ == "__main__":
    configure()
    import handlers
    from db import models
    from db.engine import get_session, engine

    bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])

    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        asyncio.run(grpc_gate.server.serve(db_initializer=get_session, bot=bot))
    elif sys.argv[1] == "poll":
        bot.message_handler(commands=["register_me"])(handlers.register_for_blog(db_initializer=get_session))

        # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
        bot.message_handler(func=lambda message: True)(handlers.echo_message)

        asyncio.run(bot.polling(request_timeout=1000))
    elif sys.argv[1] == "dbpush":
        async def db_create_all():
            async with engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.drop_all)
                await conn.run_sync(models.Base.metadata.create_all)
        asyncio.run(db_create_all())
