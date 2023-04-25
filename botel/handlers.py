import asyncio
import logging
from enum import Enum
from typing import AsyncGenerator, Callable

import grpc
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ChatMemberUpdated,
)

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


class QUERY_DATA(str, Enum):
    """
    The constants that query callbacks use
    """
    REGISTER_CHANEL = "add_a_channel"
    CANCEL = "cancel"


class STATES(str, Enum):
    """
    The possible states
    """
    REGISTERING_CHANEL = "add_a_channel"


markup = InlineKeyboardMarkup()
itembtn1 = InlineKeyboardButton(
    "add a channel", callback_data=QUERY_DATA.REGISTER_CHANEL.value
)
markup.add(itembtn1)
MENUE_MARKUP = markup


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


async def menu(message: Message, data, bot: AsyncTeleBot):
    """
    Send the menu inline keyboard
    """
    await bot.send_message(
        message.chat.id, "Choose one option:", reply_markup=MENUE_MARKUP
    )


async def add_to_a_channel_state(message: CallbackQuery, data, bot: AsyncTeleBot):
    """
    Set or Unset the user's state on adding a channel and send the appropriate message
    """
    if message.data == QUERY_DATA.CANCEL.value:
        t1 = bot.delete_state(message.from_user.id)

        t2 = bot.edit_message_text(
            "Adding channel cancelled, choose one option:",
            message.message.chat.id,
            message.message.id,
            reply_markup=MENUE_MARKUP,
        )
        await asyncio.gather(t1, t2)
        return
    markup = InlineKeyboardMarkup()
    itembtna = InlineKeyboardButton("Cancel", callback_data=QUERY_DATA.CANCEL.value)
    markup.row(itembtna)
    t1 = bot.edit_message_text(
        "Add the bot to your channel and then send us a forwarded message from that channel",
        chat_id=message.message.chat.id,
        message_id=message.message.id,
        reply_markup=markup,
    )
    t2 = bot.set_state(message.from_user.id, STATES.REGISTERING_CHANEL.value)
    await asyncio.gather(t1, t2)


async def add_to_a_channel(message: Message, data, bot: AsyncTeleBot):
    """
    Tries to add the channel that it's message is forwarded
    """
    bot_user = await bot.get_me()
    try:
        bot_channel_membership = await bot.get_chat_member(
            message.forward_from_chat.id, bot_user.id
        )
    except ApiTelegramException as e:
        if e.error_code == 403:
            markup = InlineKeyboardMarkup()
            itembtn1 = InlineKeyboardButton("try again", callback_data="add_a_channel")
            markup.add(itembtn1)
            t1 = bot.send_message(
                message.chat.id,
                "you are not added the bot yet. Cancelled",
                reply_markup=markup,
            )
            t2 = bot.delete_state(message.from_user.id)
            await asyncio.gather(t1, t2)
            return
        raise
    if bot_channel_membership:
        channel = await bot.get_chat(message.forward_from_chat.id)
        # TODO register the channel
        return


async def echo_bot_chat_events(update: ChatMemberUpdated, data, bot: AsyncTeleBot):
    """
    Complaines whenever the bot's rights are given away from it
    Confirms rights are given to the bot
    """
    logging.info(str(update.difference))


async def channel_post(update: Message, data, bot: AsyncTeleBot):
    """
    Prepare the channel post to be commentable
    """
    logging.info("channel_post received")


async def group_messages(update: Message, data, bot: AsyncTeleBot):
    """
    Handle group messages
    """
    logging.info("group_messages received")


async def group_replies(update: Message, data, bot: AsyncTeleBot):
    """
    Handle group reply messages
    """
    logging.info(str(update.difference))
