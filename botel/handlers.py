import asyncio
import logging
from contextlib import AsyncExitStack
from enum import Enum
from typing import Any, AsyncContextManager, Callable, Mapping

import grpc
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from grpc.aio._channel import Channel
from say_protos import comments_pb2, comments_pb2_grpc, webpage_pb2, webpage_pb2_grpc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from botel import dal
from botel.dal.chat import register_channel_and_linked_group
from botel.dal.user import is_logged_in, is_temped_in, login, logout, temp_in
from botel.db.engine import SessionContextManager
from botel.db.operations.create import register_instance
from botel.utils.telegram import get_start_param


def injector(*initializers: tuple[Callable[[Any], AsyncContextManager], tuple]):
    """
    Inject AsyncContextManagers to the bot handlers in the order provided
    """

    def get_injects(func):
        # Don't use wraps, changing the func signature
        async def wrapper(message, data, bot):
            async with AsyncExitStack() as stack:
                managers = [
                    await stack.enter_async_context(initializer[0](*initializer[1]))
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
    LOGOUT = "logout"
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
itembtn2 = InlineKeyboardButton("Logout", callback_data=QUERY_DATA.LOGOUT.value)
markup.add(itembtn1, itembtn2, row_width=1)
MENUE_MARKUP = markup


def register_handlers(
    telebot: AsyncTeleBot,
    configs: Mapping,
    db_initializer: tuple[
        Callable[[sessionmaker], SessionContextManager], sessionmaker
    ],
    grpc_initializer: tuple[Callable[[str], AsyncContextManager[Channel]], str],
):
    # Private
    @telebot.message_handler(commands=["register_me"])
    @injector((db_initializer[0], (db_initializer[1],)))
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
    @injector((db_initializer[0], (db_initializer[1],)))
    async def menu(db: AsyncSession, message: Message, data, bot: AsyncTeleBot):
        """
        Send the menu inline keyboard
        """
        if not await is_logged_in(db, message.chat.id):
            markup = InlineKeyboardMarkup()
            itembtn1 = InlineKeyboardButton(
                "Login",
                url=f"http://{configs['wagtail_url']}/admin/linking/telebot/{bot.user.username}/",
            )
            markup.add(itembtn1)
            await bot.send_message(
                message.chat.id,
                "Do you have an account that we can recover you data from:",
                reply_markup=markup,
            )
            return
        await bot.send_message(
            message.chat.id, "Choose one option:", reply_markup=MENUE_MARKUP
        )

    @telebot.message_handler(
        commands=["start"],
        chat_types=["private"],
        func=lambda message: get_start_param(message).split("_")[0] == "linkUserPK",
    )
    @injector((db_initializer[0], (db_initializer[1],)))
    async def link_to_wagtail(
        db: AsyncSession, message: Message, data, bot: AsyncTeleBot
    ):
        fragment = get_start_param(message).split("_")[1]
        transport = AIOHTTPTransport(url=f"http://{configs['wagtail_url']}/graphql/")
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(
                """
                query ($theUuid: String!) {
                  retrieveUserByPrivateFragment(theUuid: $theUuid) {
                    id
                  }
                }
                """
            )

            result = await session.execute(query, variable_values={"theUuid": fragment})
        _ = await login(
            db=db,
            chat_id=message.chat.id,
            user_id=int(result["retrieveUserByPrivateFragment"]["id"]),
        )
        await bot.send_message(
            message.chat.id,
            "Your SayIf and Telegram accounts are now linked",
            reply_markup=MENUE_MARKUP,
        )

    @telebot.callback_query_handler(
        # chat_types=["private"],
        func=lambda x: x.data
        == QUERY_DATA.LOGOUT.value
    )
    @injector((db_initializer[0], (db_initializer[1],)))
    async def unlink_from_wagtail(
        db: AsyncSession, message: CallbackQuery, data, bot: AsyncTeleBot
    ):
        _ = await logout(db=db, chat_id=message.message.chat.id)
        markup = InlineKeyboardMarkup()
        itembtn1 = InlineKeyboardButton(
            "Login",
            url=f"http://{configs['wagtail_url']}/admin/linking/telebot/{bot.user.username}/",
        )
        markup.add(itembtn1)
        await bot.send_message(
            message.message.chat.id,
            "You are not logged in:",
            reply_markup=markup,
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
    @injector((db_initializer[0], (db_initializer[1],)))
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
    @injector((db_initializer[0], (db_initializer[1],)))
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
    @injector(
        (db_initializer[0], (db_initializer[1],)),
        (grpc_initializer[0], (grpc_initializer[1],)),
    )
    async def group_replies(
        db: AsyncSession, keeper_chan: Channel, update: Message, data, bot: AsyncTeleBot
    ):
        """
        Handle group reply messages
        """
        u1 = await is_logged_in(db, update.from_user.id)
        u2 = await is_temped_in(db, update.from_user.id)
        if not u1 and not u2:
            t_profile = await bot.get_user_profile_photos(update.from_user.id, limit=1)
            if t_profile.photos:
                main_profile_file_id = t_profile.photos[0][-1].file_id
                t_profile_url = await bot.get_file_url(main_profile_file_id)
            chat, _ = await temp_in(
                db,
                configs=configs,
                t_user=update.from_user,
                t_profile_url=t_profile_url,
            )
        elif u1:
            chat = u1
        else:
            chat = u2

        stub = comments_pb2_grpc.CommentingStub(keeper_chan)
        reply_to_id = (
            f"{update.reply_to_message.id}-{update.reply_to_message.chat.id}"
            if not update.reply_to_message.forward_from_message_id
            else 0
        )
        posted_comment = await stub.Post(
            comments_pb2.Comment(
                reply_to_id=reply_to_id,
                user_id=chat.user_id,
                content=update.text,
                outer_identifier=f"{update.id}/{update.chat.id}",
            )
        )

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
