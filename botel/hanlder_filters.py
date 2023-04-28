from sqlalchemy.ext.asyncio import AsyncSession
from telebot.types import Message

from botel.dal import is_commentable


async def commentable_filter(db: AsyncSession, message: Message) -> bool:
    return message.reply_to_message and await is_commentable(
        db=db,
        group_id=message.chat.id,
        message_id=message.reply_to_message.forward_from_message_id,
    )
