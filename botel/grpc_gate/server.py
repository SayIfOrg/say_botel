# from concurrent import futures
import asyncio
import logging
import os
from contextlib import AsyncExitStack
from typing import AsyncGenerator, Callable

import grpc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from telebot.async_telebot import AsyncTeleBot

from say_protos import webpage_pb2, webpage_pb2_grpc

from botel.db.engine import SessionContextManager
from botel.utils.normalize import clean_html
from botel.db.operations import create


def injector(*initializers: str):
    """
    Inject AsyncContextManagers to the Servicer methods in the provided order
    """

    def get_injects(func):
        # Don't use wraps, changing the func signature
        async def wrapper(self, request, context):
            async with AsyncExitStack() as stack:
                managers = [
                    await stack.enter_async_context(getattr(self, initializer)())
                    for initializer in initializers
                ]
                return await func(self, request, context, *managers)

        return wrapper

    return get_injects


class PageServicer(webpage_pb2_grpc.PageServicer):
    def __init__(
        self,
        db_initializer: tuple[Callable[[sessionmaker], SessionContextManager], sessionmaker],
    ):
        self.db_initializer = db_initializer

    @injector("db_initializer")
    async def PublishSuperPage(self, request, context, db: AsyncSession):
        telebot = AsyncTeleBot(os.environ["TELEGRAM_TOKEN"])  # TODO make this dynamic
        final_coroutines = []
        message = clean_html(request.body)
        previous_published_messages = []
        if request.edit_originals or request.reference_original:
            previous_published_messages = list(
                await create.get_page_records(db, request.id)
            )
        if request.edit_originals:
            final_coroutines.extend(
                [
                    telebot.edit_message_text(
                        text=message,
                        chat_id=request.chat_id,
                        message_id=i.message_id,
                        parse_mode="html",
                    )
                    for i in previous_published_messages
                ]
            )
        if not request.just_edit:
            new_message = await telebot.send_message(
                chat_id=request.chat_id,
                text=message,
                parse_mode="html",
                reply_to_message_id=previous_published_messages[0].message_id
                if request.reference_original and previous_published_messages
                else None,
            )
            final_coroutines.append(
                create.publish_record(db, page_id=request.id, message_id=new_message.id)
            )
        g_ress = await asyncio.gather(*final_coroutines, return_exceptions=True)
        for res in g_ress:
            if isinstance(res, Exception):
                print(res)
        return webpage_pb2.Result(message="OK")


class ManageInstanceServicer(webpage_pb2_grpc.ManageInstanceServicer):
    def __init__(
        self, db_initializer: tuple[Callable[[sessionmaker], SessionContextManager], sessionmaker]
    ):
        self.db_initializer = db_initializer

    @injector("db_initializer")
    async def InstanceList(self, request, context, db):
        instances = list(await create.get_project_instances(db, request.id))
        return webpage_pb2.Instances(
            instances=[
                {"id": i.id, "title": "title", "type": "type"} for i in instances
            ]
        )

    @injector("db_initializer")
    async def InstanceDetail(self, request, context, db):
        instance = await create.get_instance(db, request.id)
        return webpage_pb2.Instance(id=instance.id, title="title", type="type")


async def serve(db_initializer: tuple[Callable[[], SessionContextManager], sessionmaker]):
    logging.basicConfig()
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = grpc.aio.server()
    webpage_pb2_grpc.add_PageServicer_to_server(
        PageServicer(db_initializer=db_initializer), server
    )
    webpage_pb2_grpc.add_ManageInstanceServicer_to_server(
        ManageInstanceServicer(db_initializer=db_initializer), server
    )
    server.add_insecure_port("[::]:5060")
    # server.start()
    await server.start()
    # server.wait_for_termination()
    await server.wait_for_termination()
