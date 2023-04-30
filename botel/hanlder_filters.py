from typing import Callable, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from telebot.asyncio_filters import SimpleCustomFilter
from telebot.types import Message

from botel.dal import is_commentable
from botel.utils.common import method_injector


async def commentable_filter(db: AsyncSession, message: Message) -> bool:
    return message.reply_to_message and await is_commentable(
        db=db,
        group_id=message.chat.id,
        message_id=message.reply_to_message.forward_from_message_id,
    )


class IsCommentingFilter(SimpleCustomFilter):
    """
    Checking if a message is considered to be part of commenting feature
    """

    def __init__(
        self, db_initializer: Callable[[], AsyncGenerator[AsyncSession, None]]
    ):
        self.db_initializer = db_initializer

    key = "is_commentable"

    @method_injector("db_initializer")
    async def check(self, db: AsyncSession, message: Message):
        return await commentable_filter(db=db, message=message)
