from typing import AsyncContextManager, Callable

from grpc._cython.cygrpc import Channel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from telebot.asyncio_filters import SimpleCustomFilter
from telebot.types import Message

from botel.dal import is_commentable, is_replyable
from botel.db.engine import SessionContextManager
from botel.utils.common import method_injector


async def commentable_filter(
    db: AsyncSession, keeper_chan: Channel, message: Message
) -> bool:
    return message.reply_to_message and (
        await is_commentable(
            db=db,
            group_id=message.chat.id,
            message_id=message.reply_to_message.forward_from_message_id,
        )
        or await is_replyable(
            keeper_chan=keeper_chan,
            chat_id=message.reply_to_message.chat.id,
            message_id=message.reply_to_message.id,
        )
    )


class IsCommentingFilter(SimpleCustomFilter):
    """
    Checking if a message is considered to be part of commenting feature
    """

    def __init__(
        self,
        db_initializer: tuple[
            Callable[[sessionmaker], SessionContextManager], sessionmaker
        ],
        grpc_initializer: tuple[Callable[[str], AsyncContextManager[Channel]], str],
    ):
        self.db_initializer = db_initializer[0], (db_initializer[1],)
        self.grpc_initializer = grpc_initializer[0], (grpc_initializer[1],)

    key = "is_commentable"

    @method_injector("db_initializer", "grpc_initializer")
    async def check(self, db: AsyncSession, keeper_chan: Channel, message: Message):
        return await commentable_filter(db=db, keeper_chan=keeper_chan, message=message)
