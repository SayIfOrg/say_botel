# from concurrent import futures
import logging
import grpc


from . import webpage_pb2
from . import webpage_pb2_grpc

from main import bot
from utils.normalize import clean_html


class PublishServicer(webpage_pb2_grpc.PublishServicer):
    async def PublishRichText(self, request, context):
        message = clean_html(request.body)
        res = await bot.send_message(chat_id=73789947, text=message, parse_mode="html")
        return webpage_pb2.Result(message="OK")


async def serve():
    logging.basicConfig()
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = grpc.aio.server()
    webpage_pb2_grpc.add_PublishServicer_to_server(PublishServicer(), server)
    server.add_insecure_port("[::]:5060")
    # server.start()
    await server.start()
    # server.wait_for_termination()
    await server.wait_for_termination()
