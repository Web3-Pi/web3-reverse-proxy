from __future__ import annotations

import socket
import select
import ssl
import logging

from web3_reverse_proxy.config.conf import LISTEN_BACKLOG_PARAM, PROXY_LISTEN_ADDRESS, SSL_ENABLED, \
    SSL_CERT_FILE, SSL_KEY_FILE
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


class ServerSocket:

    def __init__(self, _socket: socket.socket) -> None:
        self.socket = _socket

    def close(self) -> None:
        self.socket.close()

    def accept(self, timeout: float | None = None) -> ClientSocket:
        res = None

        s_read, _, _ = select.select([self.socket], [], [], timeout)
        if len(s_read) > 0:
            try:
                s_src, _ = self.socket.accept()
                res = ClientSocket.from_socket(s_src)
            except(ssl.SSLError) as ssl_err:
                logging.error(ssl_err)
                res = None

        return res

    @classmethod
    def create(cls,
               listen_port: int,
               listen_backlog_param: int = LISTEN_BACKLOG_PARAM,
               timeout=None) -> ServerSocket:

        s_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_srv.bind((PROXY_LISTEN_ADDRESS, listen_port))
        s_srv.listen(listen_backlog_param)
        if SSL_ENABLED:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(SSL_CERT_FILE, SSL_KEY_FILE)
            s_srv = context.wrap_socket(s_srv, server_side=True)

        if timeout:
            s_srv.settimeout(timeout)

        return ServerSocket(s_srv)
