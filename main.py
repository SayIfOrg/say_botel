import asyncio
import os
import sys

import grpc
from telebot.async_telebot import AsyncTeleBot

from db.operations.create import register_instance
from grpc_gate import webpage_pb2, webpage_pb2_grpc
import grpc_gate.server


bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])
if __name__ == "__main__":
    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        asyncio.run(grpc_gate.server.serve())
    elif sys.argv[1] == "poll":

        @bot.message_handler(commands=["register_me"])
        async def register_for_blog(message):
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
                        _ = await register_instance(response.id, 1, message.chat)
                    await bot.reply_to(
                        message, "succeeded" if response.name else "Error"
                    )
                    return
                await bot.reply_to(message, "It's not valid")

        # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
        @bot.message_handler(func=lambda message: True)
        async def echo_message(message):
            await bot.reply_to(message, message.text)

        asyncio.run(bot.polling(request_timeout=1000))
