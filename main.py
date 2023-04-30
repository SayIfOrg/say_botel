import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from telebot.asyncio_filters import StateFilter
from telebot.async_telebot import AsyncTeleBot

import botel.grpc_gate.server
from botel.grpc_gate.client import get_channel
from botel.hanlder_filters import IsCommentingFilter


def configure():
    load_dotenv(dotenv_path=".env", override=True)


async def amain():
    configure()
    from botel.handlers import register_handlers
    from botel.db import models
    from botel.db.engine import get_session, engine
    from botel.grpc_gate import server

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
            telebot.add_custom_filter(IsCommentingFilter(db_initializer=get_session))
            register_handlers(telebot, get_session, get_channel)
            poll_task = asyncio.create_task(telebot.polling(request_timeout=1000))
            poll_tasks.append(poll_task)
        await asyncio.gather(*poll_tasks)
    elif sys.argv[1] == "dbpush":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(amain())
