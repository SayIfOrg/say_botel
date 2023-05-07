from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def get_engine(db_conn_url: str):
    engine = create_async_engine(
        db_conn_url,
        echo=True,
    )
    return engine


def get_sessionmaker(engine) -> sessionmaker:
    DBSession = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return DBSession


SessionContextManager = AsyncContextManager[AsyncSession]


@asynccontextmanager
async def get_session(db_session: sessionmaker) -> SessionContextManager:
    async with db_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            # Maybe it's not required ,and it is already done by sqlalchemy
            await session.close()
