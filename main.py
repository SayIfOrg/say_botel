import asyncio
import sys
import os

import grpc_gate.server
from telebot.async_telebot import AsyncTeleBot


bot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])
if __name__ == "__main__":
    if sys.argv[1] == "grpc":
        # grpc_gate.server.serve()
        asyncio.run(grpc_gate.server.serve())
    elif sys.argv[1] == "poll":

        @bot.message_handler(commands=["help", "start"])
        async def send_welcome(message):
            await bot.reply_to(
                message,
                """\
        Hi there, I am EchoBot.
        I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
        """,
            )

        # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
        @bot.message_handler(func=lambda message: True)
        async def echo_message(message):
            await bot.reply_to(message, message.text)

        asyncio.run(bot.polling(request_timeout=1000))
