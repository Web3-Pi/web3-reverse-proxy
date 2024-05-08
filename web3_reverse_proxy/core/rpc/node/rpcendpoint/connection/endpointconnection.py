from __future__ import annotations

from dataclasses import dataclass

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import EndpointConnectionStats
from web3_reverse_proxy.core.sockets.basesocket import BaseSocket

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver, ResponseReceiverGeth
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender

from web3_reverse_proxy.utils.logger import get_logger


@dataclass
class EndpointConnection:

    socket: BaseSocket

    req_sender: RequestSender
    res_receiver: ResponseReceiver

    ip: str
    host: str
    port: int
    is_ssl: bool

    stats: EndpointConnectionStats

    _logger = get_logger("EndpointConnection")


    @classmethod
    def create(cls, conn_descr: EndpointConnectionDescriptor) -> EndpointConnection:
        cls._logger.debug(f"Creating socket based on description: {conn_descr}")
        sock = BaseSocket.create_socket(conn_descr.host, conn_descr.port, conn_descr.is_ssl)
        cls._logger.debug(f"Socket created for description: {conn_descr}")
        ip = sock.get_peer_name()[0]

        req_sender = RequestSender(sock, conn_descr.host, conn_descr.auth_key)

        is_ssl = conn_descr.is_ssl

        res_receiver = ResponseReceiverGeth(sock)

        stats = EndpointConnectionStats()

        return EndpointConnection(sock, req_sender, res_receiver, ip, conn_descr.host, conn_descr.port, is_ssl, stats)

    def close(self) -> None:
        self.socket.close()
