import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import grpc
from grpc.aio._channel import Channel


@asynccontextmanager
async def get_channel() -> AsyncGenerator[Channel, None]:
    async with grpc.aio.insecure_channel(os.environ["KEEPER_GRPC_URL"]) as channel:
        yield channel
