from __future__ import annotations

import ssl
from dataclasses import dataclass

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import EndpointConnectionStats
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.basesocket import BaseSocket

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver, ResponseReceiverSSL, ResponseReceiverGeth
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender


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

    def send_recv_roundtrip(self, req: RPCRequest) -> RPCResponse:
        req_bytes = self.req_sender.send_request(req)
        res_bytes = self.res_receiver.recv_response()

        self.stats.update(req_bytes, res_bytes)

        return RPCResponse(res_bytes)

    @classmethod
    def create(cls, conn_descr: EndpointConnectionDescriptor) -> EndpointConnection:
        sock = BaseSocket.create_socket(conn_descr.host, conn_descr.port, conn_descr.is_ssl)
        ip = sock.get_peer_name()[0]

        req_sender = RequestSender(sock, conn_descr.host, conn_descr.auth_key)

        is_ssl = conn_descr.is_ssl
        if is_ssl:
            res_receiver = ResponseReceiverSSL(sock)
        else:
            res_receiver = ResponseReceiverGeth(sock)

        stats = EndpointConnectionStats()

        return EndpointConnection(sock, req_sender, res_receiver, ip, conn_descr.host, conn_descr.port, is_ssl, stats)
