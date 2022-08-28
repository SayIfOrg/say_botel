# from concurrent import futures
import asyncio
import logging
import grpc

from . import webpage_pb2
from . import webpage_pb2_grpc

from main import bot
from utils.normalize import clean_html
from db.operations import create


class PageServicer(webpage_pb2_grpc.PageServicer):
    async def PublishSuperPage(self, request, context):
        final_coroutines = []
        message = clean_html(request.body)
        previous_published_messages = []
        if request.edit_originals or request.reference_original:
            previous_published_messages = list(
                await create.get_page_records(request.id)
            )
        if request.edit_originals:
            final_coroutines.extend(
                [
                    bot.edit_message_text(
                        text=message,
                        chat_id=request.chat_id,
                        message_id=i.message_id,
                        parse_mode="html",
                    )
                    for i in previous_published_messages
                ]
            )
        if not request.just_edit:
            new_message = await bot.send_message(
                chat_id=request.chat_id,
                text=message,
                parse_mode="html",
                reply_to_message_id=previous_published_messages[0].message_id
                if request.reference_original and previous_published_messages
                else None,
            )
            final_coroutines.append(
                create.publish_record(page_id=request.id, message_id=new_message.id)
            )
        await asyncio.gather(*final_coroutines)
        return webpage_pb2.Result(message="OK")


async def serve():
    logging.basicConfig()
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = grpc.aio.server()
    webpage_pb2_grpc.add_PageServicer_to_server(PageServicer(), server)
    server.add_insecure_port("[::]:5060")
    # server.start()
    await server.start()
    # server.wait_for_termination()
    await server.wait_for_termination()
