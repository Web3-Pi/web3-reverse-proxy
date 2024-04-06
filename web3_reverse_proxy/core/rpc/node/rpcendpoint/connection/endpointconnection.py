from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Callable

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import EndpointConnectionStats
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.basesocket import BaseSocket

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver, ResponseReceiverSSL, ResponseReceiverGeth
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

    def _get_receiver_response_handler(
            self,
            req: RPCRequest,
            req_bytes: bytearray,
            outer_handler: Callable
        ) -> Callable:
        def receiver_response_handler(res_bytes: bytearray):
            self.stats.update(req_bytes, res_bytes)
            return outer_handler(RPCResponse(res_bytes, req))
        return receiver_response_handler

    def reconnect(self):
        self.socket.close()

        try:
            self.socket = self.socket.create_socket(self.ip, self.port, self.is_ssl)
        except ssl.SSLCertVerificationError:
            self.socket.clear_mapping(self.host)
            self.socket = self.socket.create_socket(self.host, self.port, self.is_ssl)
        except Exception:
            raise

        self.req_sender.update_socket(self.socket)
        self.res_receiver.update_socket(self.socket)

    def send_recv_roundtrip(self, req: RPCRequest, callback: Callable) -> None:
        self._logger.debug(f"{self} is sending request {req}")
        req_bytes = self.req_sender.send_request(req)
        self._logger.debug(f"{self} is receiving response")
        self.res_receiver.recv_response(self._get_receiver_response_handler(req, req_bytes, callback))

    @classmethod
    def create(cls, conn_descr: EndpointConnectionDescriptor) -> EndpointConnection:
        cls._logger.debug(f"Creating socket based on description: {conn_descr}")
        sock = BaseSocket.create_socket(conn_descr.host, conn_descr.port, conn_descr.is_ssl)
        cls._logger.debug(f"Socket created for description: {conn_descr}")
        ip = sock.get_peer_name()[0]

        req_sender = RequestSender(sock, conn_descr.host, conn_descr.auth_key)

        is_ssl = conn_descr.is_ssl
        if is_ssl:
            res_receiver = ResponseReceiverSSL(sock)
        else:
            res_receiver = ResponseReceiverGeth(sock)

        stats = EndpointConnectionStats()

        return EndpointConnection(sock, req_sender, res_receiver, ip, conn_descr.host, conn_descr.port, is_ssl, stats)
