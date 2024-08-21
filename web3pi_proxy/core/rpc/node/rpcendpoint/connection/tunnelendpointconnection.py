import socket
from typing import Callable

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.core.sockets.basesocket import BaseSocket


class TunnelEndpointConnection(EndpointConnection):

    def __init__(self, endpoint: RPCEndpoint, connection_factory: Callable) -> None:
        self.connection_factory = connection_factory
        super().__init__(endpoint)

    def close(self) -> None:
        self.socket.close()

    def create_socket(self) -> BaseSocket:
        s_dst: socket = self.connection_factory()
        return BaseSocket.wrap_socket(
            s_dst, self.conn_descr.host, self.conn_descr.is_ssl
        )

