from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db import models
from db.operations.engin import get_session


async def publish_record(page_id, message_id):
    async with get_session() as session:
        async with session.begin():
            session.add_all(
                [
                    models.PublishHistory(page_id=page_id, message_id=message_id),
                ]
            )
