import abc
from core.rpc.node.connection_pool import EndpointConnectionPool
from core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from core.rpc.node.rpcendpoint.connection.sender import RequestSender
from core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver

class ConnectionHandler(abc.ABC):
    def release() -> None:
        pass

    def get_sender() -> RequestSender:
        pass

    def get_receiver() -> ResponseReceiver:
        pass


class EndpointConnectionHandler(ConnectionHandler):
    def __init__(
            self,
            connection: EndpointConnection,
            connection_pool: EndpointConnectionPool
        ) -> None:
        self.connection = connection
        self.connection_pool = connection_pool

    def get_sender(self) -> RequestSender:
        return self.connection.req_sender

    def get_receiver(self) -> RequestSender:
        return self.connection.res_receiver

    def release(self) -> None:
        self.connection_pool.put(self.connection)
