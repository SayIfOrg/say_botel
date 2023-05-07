from contextlib import asynccontextmanager
from typing import AsyncGenerator

import grpc
from grpc.aio._channel import Channel


@asynccontextmanager
async def get_channel(url: str) -> AsyncGenerator[Channel, None]:
    async with grpc.aio.insecure_channel(url) as channel:
        yield channel
