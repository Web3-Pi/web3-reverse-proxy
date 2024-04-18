from abc import ABC, abstractmethod
from typing import Callable, Tuple

from web3_reverse_proxy.core.sockets.basesocket import BaseSocket
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.config.conf import Config
from web3_reverse_proxy.utils.logger import get_logger


class ResponseReceiver(ABC):

    @abstractmethod
    def recv_response(self) -> bytearray:
        pass

    @abstractmethod
    def update_socket(self, sock: BaseSocket) -> None:
        pass


class ResponseReceiverGeth(ResponseReceiver):
    _logger = get_logger("ResponseReceiverGeth")

    def __init__(self, sock: BaseSocket) -> None:
        self.socket = sock

    def recv_response(self, callback: Callable) -> None:
        response_received = False
        raw_response = bytearray()
        chunked = False

        chunked = False
        buf_size = Config.DEFAULT_RECV_BUF_SIZE

        self._logger.debug("Loop starting")
        while not response_received:
            assert self.socket.is_ready_read()

            self._logger.debug("Reading response from socket")
            data = self.socket.recv(buf_size)
            raw_response += data

            if not raw_response:
                raise IOError
            self._logger.debug(f"Raw response -> {raw_response}")
            # Chunked responses
            if chunked or RPCResponse.is_chunked(raw_response):
                if not chunked:
                    head, separator, body = raw_response.partition(RPCResponse.HEAD_SEPARATOR)
                    head += separator
                    raw_response = body
                    self._logger.debug(f"Callback {head}")
                    callback(head)
                    chunked = True

                chunks, raw_response, response_received = self._process_chunked_data(raw_response)
                for chunk in chunks:
                    self._logger.debug(f"Callback {chunk}")
                    callback(chunk)

            # Non-chunked responses
            else:
                response_received = RPCResponse.is_complete_raw_response(raw_response)
                if response_received:
                    self._logger.debug("Response completed")
                    self._logger.debug(f"Callback {raw_response}")
                    callback(raw_response)


    def update_socket(self, sock: BaseSocket) -> None:
        self.socket = sock

    @staticmethod
    def _process_chunked_data(raw_response: bytearray) -> Tuple[list, bytearray, int, bool]:
        response_completed = RPCResponse.is_complete_raw_response(raw_response)
        chunks = []

        while True:
            length, separator, content = raw_response.partition(RPCResponse.CRLF_SEPARATOR)
            if separator == b"":
                # incomplete length data
                break
            target_length = int(length, 16)
            if len(content) < target_length + 2:
                # incomplete chunk content
                break
            chunks.append(length + RPCResponse.CRLF_SEPARATOR + content[:target_length + 2])
            raw_response = content[target_length + 2:]

        return chunks, raw_response, response_completed


class ResponseReceiverSSL(ResponseReceiver):
    _logger = get_logger("ResponseReceiverSSL")

    MAX_LINE_LEN = 65536

    def __init__(self, sock: BaseSocket) -> None:
        self.rfile = sock.socket.makefile('rb', -1)

    # FIXME: this implementation is based on an assumption that the endpoint is a valid web3 endpoint (i.e. replies with
    #  valid responses only)
    def recv_response(self, callback: Callable) -> bytearray:
        fd = self.rfile
        response_data = bytearray()

        data = fd.readline(self.MAX_LINE_LEN + 1)
        response_data += data
        content_len = -1
        chunked = False

        self._logger.debug("Receiver loop starting")
        while True:
            self._logger.debug("Receiver reading response from socket")
            data = fd.readline(self.MAX_LINE_LEN + 1)
            response_data += data
            self._logger.debug(f"response data -> {response_data}")

            if data in (b'\r\n', b'\n', b''):
                break

            if data.lower().startswith(b'content-length:'):
                content_len = int(data[16:])

            if RPCResponse.is_chunked(response_data):
                chunked = True

        if response_data == b'':
            raise IOError

        if content_len > 0:
            data = fd.read(content_len)
            response_data += data
            self._logger.debug(f"Callback {response_data}")
            callback(response_data)
        else:
            assert chunked, response_data
            self._logger.debug(f"Callback {response_data}")
            callback(response_data)
            response_data = bytearray()

            while True:
                data = fd.readline(self.MAX_LINE_LEN + 1)
                self._logger.debug(f"Read chunk length data: {data}")
                chunk_len = int(data.decode(RPCResponse.RAW_ENCODING), 16)
                response_data += data

                data = fd.read(chunk_len + 2)  # +2 to read '/r/n'
                self._logger.debug(f"Read chunk content data: {data}")
                response_data += data

                self._logger.debug(f"Callback {response_data}")
                callback(response_data)

                if chunk_len == 0:
                    break

                response_data = bytearray()

    def update_socket(self, sock: BaseSocket) -> None:
        self.rfile = sock.socket.makefile('rb', -1)
