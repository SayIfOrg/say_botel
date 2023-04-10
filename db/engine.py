import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


engine = create_async_engine(
    os.environ["DB_CONNECTION_URL"],
    echo=True,
)

DBSession = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with DBSession() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            # Maybe it's not required ,and it is already done by sqlalchemy
            await session.close()
