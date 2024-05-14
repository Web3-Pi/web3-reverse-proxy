from typing import Callable

from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver


class EndpointConnectionHandler(ConnectionHandler):
    class ConnectionReleasedError(Exception):
        message = "Connection has already been released"

    def __init__(
            self,
            connection: EndpointConnection,
            connection_pool: ConnectionPool
        ) -> None:
        self.connection = connection
        self.connection_pool = connection_pool

    @staticmethod
    def _acquired_connection(func: Callable) -> Callable:
        def decorator(instance: 'EndpointConnectionHandler', *args, **kwargs):
            if instance.connection is None:
                raise instance.ConnectionReleasedError
            return func(instance, *args, **kwargs)
        return decorator

    @_acquired_connection
    def get_sender(self) -> RequestSender:
        return self.connection.req_sender

    @_acquired_connection
    def get_receiver(self) -> ResponseReceiver:
        return self.connection.res_receiver

    @_acquired_connection
    def reconnect(self) -> None:
        self.connection.reconnect()

    def release(self) -> None:
        if self.connection is not None:
            self.connection_pool.put(self.connection)
            self.connection = None

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()

    def __del__(self) -> None:
        self.release()
