# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import webpage_pb2 as webpage__pb2


class PageStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.PublishSuperPage = channel.unary_unary(
                '/webpage.Page/PublishSuperPage',
                request_serializer=webpage__pb2.SuperPage.SerializeToString,
                response_deserializer=webpage__pb2.Result.FromString,
                )


class PageServicer(object):
    """Missing associated documentation comment in .proto file."""

    def PublishSuperPage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PageServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'PublishSuperPage': grpc.unary_unary_rpc_method_handler(
                    servicer.PublishSuperPage,
                    request_deserializer=webpage__pb2.SuperPage.FromString,
                    response_serializer=webpage__pb2.Result.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'webpage.Page', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Page(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def PublishSuperPage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/webpage.Page/PublishSuperPage',
            webpage__pb2.SuperPage.SerializeToString,
            webpage__pb2.Result.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)