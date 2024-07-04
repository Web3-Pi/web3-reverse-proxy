from typing import Callable

from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    ConnectionPool,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import (
    ConnectionHandler,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import (
    EndpointConnection,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.receiver import ConnectionClosedError
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.utils.logger import get_logger


class ConnectionReleasedError(Exception):
    message = "Connection has already been released"


class BrokenConnectionError(Exception):
    message = "Connection is broken"


class BrokenFreshConnectionError(BrokenConnectionError):
    message = "Connection is broken from start or broke after first send"


class ReconnectError(BrokenConnectionError):
    message = "Error while attempting reconnect"


class EndpointConnectionHandler(ConnectionHandler):
    def __init__(
        self,
        connection: EndpointConnection,
        connection_pool: ConnectionPool,
        is_new_connection: bool = False,  # TODO: It might be a good idea to derive this from connection instead
    ) -> None:
        self.connection = connection
        self.connection_pool = connection_pool
        self.is_new_connection = is_new_connection
        self.is_reconnect_forbidden = is_new_connection

        self.__logger = get_logger(f"EndpointConnectionHandler.{id(self)}")
        self.__logger.debug(f"Created handler for connection {connection}")

    @staticmethod
    def _acquired_connection(func: Callable) -> Callable:
        def decorator(instance: "EndpointConnectionHandler", *args, **kwargs):
            if instance.connection is None:
                raise ConnectionReleasedError
            return func(instance, *args, **kwargs)

        return decorator

    @_acquired_connection
    def send(self, req: RPCRequest) -> bytearray:
        try:
            request = self.connection.req_sender.send_request(req)
            self.is_reconnect_forbidden = True
            return request
        except:
            self.__logger.error(
                f"Failed to send request {req} over connection {self.connection}"
            )

        if not self.is_reconnect_forbidden:
            try:
                self.__logger.debug(f"Reconnecting {self.connection}")
                self.connection.reconnect()
            except:
                self.__logger.error(
                    f"Connection {self.connection} failed to reconnect!"
                )
                self.__handle_broken_connection()
                raise ReconnectError
        else:
            self.__logger.error(f"Connection {self.connection} started broken!")
            self.__handle_broken_connection()
            raise BrokenFreshConnectionError

        try:
            return self.connection.req_sender.send_request(req)
        except:
            self.__logger.error(f"Connection {self.connection} is broken")
            self.__handle_broken_connection()
            raise BrokenConnectionError

    @_acquired_connection
    def receive(self, callback: Callable) -> None:
        try:
            self.connection.res_receiver.recv_response(callback)
        except ConnectionClosedError:
            raise BrokenConnectionError
        except ConnectionError:
            raise BrokenConnectionError

    def update_request_stats(self, request: RPCRequest):
        self.connection.update_endpoint_stats(request.last_queried_bytes, bytearray())

    def update_response_stats(self, response_bytes: bytearray) -> None:
        self.connection.update_endpoint_stats(bytearray(), response_bytes)

    def release(self) -> None:
        if self.connection is not None:
            self.connection_pool.put(self.connection)
            self.connection = None

    def __handle_broken_connection(self) -> None:
        self.connection_pool.handle_broken_connection(
            self.connection, self.is_new_connection
        )
        self.connection = None

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()

    def __del__(self) -> None:
        self.release()
