from __future__ import annotations

import errno
import select
import socket
import ssl

from web3pi_proxy.config.conf import Config
from web3pi_proxy.utils.logger import get_logger


class BaseSocket:
    __logger = get_logger("BaseSocket")

    HOST_IP_MAPPING = {}

    def __init__(self, _socket: socket.socket) -> None:
        self.socket = _socket

    def send_all(self, data):
        return self.socket.sendall(data)

    def recv(self, buf_size=Config.DEFAULT_RECV_BUF_SIZE):
        return self.socket.recv(buf_size)

    def get_peer_name(self):
        return self.socket.getpeername()

    # FIXME: this method may not behave as expected
    def is_connected(self):
        try:
            print(self.get_peer_name())
        except OSError as e:
            if e.errno != errno.ENOTCONN:
                raise
            connected = False
        else:
            connected = True

        return connected

    def is_ready_read(self, timeout=None):  # TODO something more effective than select
        s_read, _, _ = select.select([self.socket], [], [], timeout)

        return len(s_read) > 0

    def is_ready_write(self, timeout=None):  # TODO something more effective than select
        _, s_write, _ = select.select([], [self.socket], [], timeout)

        return len(s_write) > 0

    def close(self) -> None:
        self.socket.close()

    @classmethod
    def clear_mapping(cls, host: str) -> None:
        if host in cls.HOST_IP_MAPPING:
            cls.HOST_IP_MAPPING.pop(host)

    # FIXME: this call can fail (wrong address, endpoint no ready -> failed connection)
    @classmethod
    def create_socket(cls, host: str, port: int, is_ssl: bool) -> BaseSocket:
        # This hack allows multiple connections to a single endpoint (using mdns requires waiting some time between
        # sockets are successfully processed). Connecting with directly specified IP address solves this problem.
        # FIXME: it may fail for remote endpoints (such as infura), as there is no guarantee that the IP stays
        # FIXME: unchanged
        if host not in cls.HOST_IP_MAPPING:
            cls.HOST_IP_MAPPING[host] = socket.gethostbyname(host)

        host_ip = cls.HOST_IP_MAPPING[host]

        cls.__logger.debug("Creating socket")
        s_dst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.__logger.debug("Connecting socket")

        s_dst.settimeout(5.0)  # TODO parametrize?
        s_dst.connect((host_ip, port))
        s_dst.settimeout(None)

        cls.__logger.debug("Finished connecting socket")

        if is_ssl:
            context = ssl.create_default_context()
            s_dst = context.wrap_socket(s_dst, server_hostname=host)

        res = BaseSocket(s_dst)

        return res
