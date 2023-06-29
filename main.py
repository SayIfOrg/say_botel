import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import StateFilter

import botel.grpc_gate.server
from botel.db import models
from botel.db.engine import get_engine, get_session, get_sessionmaker
from botel.grpc_gate.client import get_channel
from botel.handlers import register_handlers
from botel.hanlder_filters import IsCommentingFilter


def configure():
    load_dotenv(dotenv_path=".env", override=False)
    config = {
        "proxy_url": os.environ.get("PROXY_URL"),
        "db_connection_url": os.environ["DB_CONNECTION_URL"],
        "keeper_grpc_url": os.environ["KEEPER_GRPC_URL"],
        "wagtail_url": os.environ["WAGTAIL_URL"],
    }
    return config


async def amain():
    config = configure()

    engine = get_engine(config["db_connection_url"])
    sessionmaker = get_sessionmaker(engine)

    if proxy_url := config["proxy_url"]:
        from telebot import asyncio_helper

        asyncio_helper.proxy = proxy_url

    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        await botel.grpc_gate.server.serve(db_initializer=(get_session, sessionmaker))
    elif sys.argv[1] == "poll":
        # multibots functionality via poll, Not ideal but possible
        async with get_session(sessionmaker) as db:
            result = await db.execute(select(models.Bot).limit(2))
            bots = result.scalars()
        poll_tasks: list[asyncio.Task] = []
        for bot in bots:
            telebot = AsyncTeleBot(bot.api_token)
            telebot.add_custom_filter(StateFilter(telebot))
            telebot.add_custom_filter(
                IsCommentingFilter(
                    db_initializer=(get_session, sessionmaker),
                    grpc_initializer=(get_channel, config["keeper_grpc_url"]),
                )
            )
            register_handlers(
                telebot,
                config,
                (get_session, sessionmaker),
                (get_channel, config["keeper_grpc_url"]),
            )
            poll_task = asyncio.create_task(
                telebot.infinity_polling(request_timeout=1000)
            )
            poll_tasks.append(poll_task)
        await asyncio.gather(*poll_tasks)
    elif sys.argv[1] == "dbpush":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.drop_all)
            await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(amain())
