from __future__ import annotations
import time

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.receiver import (
    ResponseReceiver,
    ResponseReceiverGeth,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.core.sockets.basesocket import BaseSocket
from web3pi_proxy.utils.logger import get_logger


class EndpointConnection:
    endpoint: RPCEndpoint
    socket: BaseSocket
    req_sender: RequestSender
    res_receiver: ResponseReceiver
    last_use_timestamp: int

    ip: str
    host: str
    port: int
    auth_key: str
    is_ssl: bool

    def __init__(self, endpoint: RPCEndpoint) -> None:
        self.__logger = get_logger(f"EndpointConnection.{id(self)}")
        self.endpoint = endpoint

        self.__logger.debug(f"Creating socket for endpoint: {endpoint}")
        self.socket = self.__create_socket()
        self.__logger.debug(f"Socket created for description: {self.conn_descr}")

        self.req_sender = RequestSender(
            self.socket, self.conn_descr.host, self.conn_descr.auth_key
        )

        self.res_receiver = ResponseReceiverGeth(self.socket)

        self.last_use_timestamp = time.time_ns()

    @property
    def conn_descr(self) -> EndpointConnectionDescriptor:
        return self.endpoint.conn_descr

    @property
    def ip(self) -> str:
        return self.socket.get_peer_name()[0]

    def __create_socket(self) -> BaseSocket:
        return BaseSocket.create_socket(
            self.conn_descr.host, self.conn_descr.port, self.conn_descr.is_ssl
        )

    def close(self) -> None:
        self.socket.close()

    def reconnect(self) -> None:
        self.close()
        self.socket = self.__create_socket()
        self.req_sender = RequestSender(
            self.socket, self.conn_descr.host, self.conn_descr.auth_key
        )
        self.res_receiver = ResponseReceiverGeth(self.socket)

    def update_endpoint_stats(
        self, request_bytes: bytearray, response_bytes: bytearray
    ) -> None:
        self.endpoint.update_stats(request_bytes, response_bytes)
