from typing import AsyncGenerator, Callable

import grpc
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from botel.db.operations.create import register_instance
from botel.grpc_gate import webpage_pb2_grpc, webpage_pb2


def provide_with_db(func):
    """Inject AsyncSession to bot handlers"""

    def get_injects(db_initializer: Callable[[], AsyncGenerator[AsyncSession, None]]):
        # Don't use wraps, changing the func signature
        async def wrapper(message, data, bot):
            async with db_initializer() as db:
                return await func(db, message, data, bot)

        return wrapper

    return get_injects


@provide_with_db
async def register_for_blog(db: AsyncSession, message, data, bot):
    register_token = message.text.split(" ")[1]
    async with grpc.aio.insecure_channel("localhost:5061") as channel:
        stub = webpage_pb2_grpc.ManageInstanceStub(channel)
        response = await stub.ValidateToken(
            webpage_pb2.Token(token=register_token, commit=False)
        )
        if response.name:
            response = await stub.ValidateToken(
                webpage_pb2.Token(token=register_token, commit=True)
            )
            if response.name:
                _ = await register_instance(db, response.id, 1, message.chat)
            await bot.reply_to(message, "succeeded" if response.name else "Error")
            return
        await bot.reply_to(message, "It's not valid")


async def echo_message(message: Message, data, bot: AsyncTeleBot):
    await bot.reply_to(message, message.text)
