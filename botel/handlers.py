import asyncio
import logging
from contextlib import AsyncExitStack
from enum import Enum
from typing import AsyncGenerator, Callable, Any

import grpc
from grpc.aio._channel import Channel
from sayif_protos import webpage_pb2_grpc, webpage_pb2, comments_pb2, comments_pb2_grpc
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberUpdated,
)

from botel import dal
from botel.dal.chat import register_channel_and_linked_group, is_commentable
from botel.db.operations.create import register_instance
from botel.hanlder_filters import commentable_filter
from botel.utils.common import injector as common_injector


def injector(*initializers: Callable[[], AsyncGenerator[Any, None]]):
    """
    Inject AsyncContextManagers to the bot handlers in the order provided
    """

    def get_injects(func):
        # Don't use wraps, changing the func signature
        async def wrapper(message, data, bot):
            async with AsyncExitStack() as stack:
                managers = [
                    await stack.enter_async_context(initializer())
                    for initializer in initializers
                ]
                return await func(*managers, message, data, bot)

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


def register_handlers(
    telebot: AsyncTeleBot,
    db_initializer: Callable[[], AsyncGenerator[AsyncSession, None]],
    grpc_initializer: Callable[[], AsyncGenerator[Channel, None]],
):
    # Private
    @telebot.message_handler(commands=["register_me"])
    @injector(db_initializer)
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

    @telebot.message_handler(commands=["m"])
    async def menu(message: Message, data, bot: AsyncTeleBot):
        """
        Send the menu inline keyboard
        """
        await bot.send_message(
            message.chat.id, "Choose one option:", reply_markup=MENUE_MARKUP
        )

    @telebot.callback_query_handler(
        func=lambda x: x.data == QUERY_DATA.REGISTER_CHANEL.value
    )
    async def add_to_a_channel_state(message: CallbackQuery, data, bot: AsyncTeleBot):
        """
        Set the user's state on adding a channel and send the appropriate message
        """
        markup = InlineKeyboardMarkup()
        itembtna = InlineKeyboardButton("Cancel", callback_data=QUERY_DATA.CANCEL.value)
        markup.row(itembtna)
        t1 = bot.edit_message_text(
            "Add the bot to your channel and then send us a forwarded message from that channel",
            chat_id=message.message.chat.id,
            message_id=message.message.id,
            reply_markup=markup,
        )
        t2 = bot.set_state(
            message.from_user.id,
            STATES.REGISTERING_CHANEL.value,
            chat_id=message.message.chat.id,
        )
        await asyncio.gather(t1, t2)

    @telebot.callback_query_handler(
        func=lambda x: x.data == QUERY_DATA.CANCEL.value,
        state=STATES.REGISTERING_CHANEL.value,
    )
    async def add_to_a_channel_state(message: CallbackQuery, data, bot: AsyncTeleBot):
        """
        Unset the user's state on adding a channel and send the appropriate message
        """
        t1 = bot.delete_state(message.from_user.id, chat_id=message.message.chat.id)

        t2 = bot.edit_message_text(
            "Adding channel cancelled, choose one option:",
            message.message.chat.id,
            message.message.id,
            reply_markup=MENUE_MARKUP,
        )
        await asyncio.gather(t1, t2)

    @telebot.message_handler(state=STATES.REGISTERING_CHANEL.value)
    @injector(db_initializer)
    async def add_to_a_channel(
        db: AsyncSession, message: Message, data, bot: AsyncTeleBot
    ):
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
                itembtn1 = InlineKeyboardButton(
                    "try again", callback_data="add_a_channel"
                )
                markup.add(itembtn1)
                t1 = bot.send_message(
                    message.chat.id,
                    "you are not added the bot yet. Cancelled",
                    reply_markup=markup,
                )
                t2 = bot.delete_state(message.from_user.id, message.chat.id)
                await asyncio.gather(t1, t2)
                return
            raise
        if bot_channel_membership:
            channel = await bot.get_chat(message.forward_from_chat.id)
            await register_channel_and_linked_group(
                db=db, channel_id=channel.id, linked_group_id=channel.linked_chat_id
            )
            t1 = bot.reply_to(message, "successfully registered")
            t2 = bot.delete_state(message.from_user.id, chat_id=message.chat.id)
            await asyncio.gather(t1, t2)

    # Chat
    @telebot.my_chat_member_handler(func=lambda x: True)
    async def echo_bot_chat_events(update: ChatMemberUpdated, data, bot: AsyncTeleBot):
        """
        Complaines whenever the bot's rights are given away from it
        Confirms rights are given to the bot
        """
        logging.info(str(update.difference))

    @telebot.channel_post_handler(func=lambda x: True)
    @injector(db_initializer)
    async def channel_post(db: AsyncSession, update: Message, data, bot: AsyncTeleBot):
        """
        Add the channel post to be commentable
        """
        await dal.register_commentable(
            db, message_id=update.message_id, channel_id=update.chat.id
        )

    # # Group
    @telebot.message_handler(
        is_commentable=True,
        chat_types=["supergroup"],
    )
    @injector(grpc_initializer)
    async def group_replies(
        keeper_chan: Channel, update: Message, data, bot: AsyncTeleBot
    ):
        """
        Handle group reply messages
        """

        stub = comments_pb2_grpc.CommentingStub(keeper_chan)
        posted_comment = await stub.Post(
            comments_pb2.Comment(
                id=0, user_id=1, content=update.text, outer_identifier=str(update.id)
            )
        )
        logging.info(f"commented {posted_comment.id}")

    #     do the commenting

    @telebot.message_handler(chat_types=["supergroup"])
    async def group_messages(update: Message, data, bot: AsyncTeleBot):
        """
        Handle group messages
        """
        logging.info("group_messages received")

    # # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
    @telebot.message_handler(func=lambda message: True)
    async def echo_message(message: Message, data, bot: AsyncTeleBot):
        await bot.reply_to(message, message.text)
