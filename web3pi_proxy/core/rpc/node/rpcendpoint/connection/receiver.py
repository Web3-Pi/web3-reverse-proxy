from abc import ABC, abstractmethod
from typing import Callable

from httptools import HttpResponseParser

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.sockets.basesocket import BaseSocket
from web3pi_proxy.utils.logger import get_logger


class HttpResponseParserListener:

    def __init__(self) -> None:
        self.need_more_data = True
        self.chunk_completed = False

    def on_message_complete(
        self,
    ):  # non-chunked message or the last response of chunked message
        self.need_more_data = False

    def on_chunk_header(self):
        self.chunk_completed = False  # in case there are more than one chunk in the response, not a perfect solution

    def on_chunk_complete(self):
        self.chunk_completed = False


class ConnectionClosedError(Exception):
    message = "Connection is closed"


class ResponseReceiver(ABC):

    @abstractmethod
    def recv_response(self, callback: Callable) -> None:
        pass

    @abstractmethod
    def update_socket(self, sock: BaseSocket) -> None:
        pass


class ResponseReceiverGeth(ResponseReceiver):
    __logger = get_logger("ResponseReceiverGeth")

    def __init__(self, sock: BaseSocket) -> None:
        self.socket = sock

    def recv_response(self, callback: Callable) -> None:
        buf_size = Config.DEFAULT_RECV_BUF_SIZE

        response_listener = HttpResponseParserListener()
        response_parser = HttpResponseParser(response_listener)

        self.__logger.debug("Loop starting")
        while response_listener.need_more_data:
            if not self.socket.is_ready_read(5):  # TODO parametrize?
                raise ConnectionClosedError
            data = self.socket.recv(buf_size)
            if not data:
                raise ConnectionClosedError
            response_parser.feed_data(data)
            self.__logger.debug(f"Raw response -> {data}")
            callback(data)

        self.__logger.debug("Response completed")

    def update_socket(self, sock: BaseSocket) -> None:
        self.socket = sock
