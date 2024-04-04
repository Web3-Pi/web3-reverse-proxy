from __future__ import annotations

import socket
import select

from web3_reverse_proxy.config.conf import Config
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
            s_src, _ = self.socket.accept()
            res = ClientSocket.from_socket(s_src)

        return res

    @classmethod
    def create(cls,
               listen_port: int,
               listen_backlog_param: int = Config.LISTEN_BACKLOG_PARAM,
               timeout=None) -> ServerSocket:

        s_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_srv.bind((Config.PROXY_LISTEN_ADDRESS, listen_port))
        s_srv.listen(listen_backlog_param)

        if timeout:
            s_srv.settimeout(timeout)

        return ServerSocket(s_srv)
