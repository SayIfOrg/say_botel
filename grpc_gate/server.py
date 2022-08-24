# from concurrent import futures
import logging
import grpc


from . import helloworld_pb2
from . import helloworld_pb2_grpc

from main import bot
from utils.normalize import clean_html


class MYServicer(helloworld_pb2_grpc.GreeterServicer):
    async def SayHello(self, request, context):
        response = helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)
        await bot.send_message(chat_id=73789947, text=request.name)
        return response

    async def PublishRichText(self, request, context):
        response = helloworld_pb2.HelloReply(message="Hello, %s!" % "OK")
        message = clean_html(request.body)
        await bot.send_message(chat_id=73789947, text=message, parse_mode="html")
        return response


async def serve():
    logging.basicConfig()
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = grpc.aio.server()
    helloworld_pb2_grpc.add_GreeterServicer_to_server(MYServicer(), server)
    server.add_insecure_port("[::]:5060")
    # server.start()
    await server.start()
    # server.wait_for_termination()
    await server.wait_for_termination()
