from __future__ import annotations

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.sockets.basesocket import BaseSocket


class ClientSocket(BaseSocket):

    def __init__(self, _socket) -> None:
        super().__init__(_socket)

        self.rfile = _socket.makefile("rb", -1)

    def recv_discard_data(self) -> None:
        ready_read = self.is_ready_read()
        assert ready_read

        self.socket.recv(Config.DEFAULT_RECV_BUF_SIZE)

    def close(self) -> None:
        self.rfile.close()
        super().close()  # self.socket.close() -- FIXME: really necessary (perhaps depends on the underlying OS)?

    def get_read_fd(self):
        return self.rfile

    def get_peer_name(self):
        return self.socket.getpeername()

    @classmethod
    def from_socket(cls, raw_socket) -> ClientSocket:
        return ClientSocket(raw_socket)
