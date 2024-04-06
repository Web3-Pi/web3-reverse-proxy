from abc import ABC, abstractmethod
from typing import Callable, Tuple

from web3_reverse_proxy.core.sockets.basesocket import BaseSocket
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.config.conf import DEFAULT_RECV_BUF_SIZE
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
        buf_size = DEFAULT_RECV_BUF_SIZE

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
                raw_response_array = raw_response.split(RPCResponse.CRLF_SEPARATOR)

                if not chunked:
                    content_sparator_index = raw_response_array.index(b'')
                    headers = raw_response_array[:content_sparator_index]
                    raw_response_array = raw_response_array[content_sparator_index + 1:]
                    chunked = True

                    headers_data = b""
                    for header in headers:
                        headers_data += header + RPCResponse.CRLF_SEPARATOR
                    headers_data += RPCResponse.CRLF_SEPARATOR
                    callback(headers_data)

                if raw_response.endswith(RPCResponse.CRLF_SEPARATOR):
                    # Remove extra empty element after split
                    raw_response_array.pop(-1)

                chunks, raw_response, buf_size, response_received = self._process_chunked_data(raw_response, raw_response_array)
                for chunk in chunks:
                    callback(chunk)

            # Non-chunked responses
            else:
                response_received = RPCResponse.is_complete_raw_response(raw_response)
                if response_received:
                    self._logger.debug("Response completed")
                    callback(raw_response)


    def update_socket(self, sock: BaseSocket) -> None:
        self.socket = sock

    @staticmethod
    def _process_chunked_data(raw_response: bytearray, chunked_elements: list) -> Tuple[list, bytearray, int, bool]:
        response_completed = RPCResponse.is_complete_raw_response(raw_response)
        target_chunk_content_length = 10 ** 6  # arbitrarily large number to compare against buffer size
        current_chunk = bytearray()
        current_chunk_content_length = 0

        if not response_completed:
            # full length/content pairs
            if len(chunked_elements) % 2 == 0:
                target_chunk_content_length = int(chunked_elements[-2], 16)
                # incomplete last chunk
                if len(chunked_elements[-1]) != target_chunk_content_length or \
                        not raw_response.endswith(RPCResponse.CRLF_SEPARATOR) or \
                        target_chunk_content_length == 0 and \
                        not response_completed:
                    current_chunk = chunked_elements[-2] + RPCResponse.CRLF_SEPARATOR + chunked_elements[-1]
                    current_chunk_content_length = len(chunked_elements[-1])
                    chunked_elements = chunked_elements[:-2]
                # complete chunk, further length unknown
                else:
                    target_chunk_content_length = 10 ** 6
            # missing last chunk content
            elif raw_response.endswith(RPCResponse.CRLF_SEPARATOR):
                target_chunk_content_length = int(chunked_elements[-1], 16)
                current_chunk = chunked_elements.pop(-1) + RPCResponse.CRLF_SEPARATOR
            # incomplete chunk length
            else:
                current_chunk = chunked_elements.pop(-1)

        complete_chunks = [
            chunked_elements[i] + RPCResponse.CRLF_SEPARATOR + chunked_elements[i + 1] + RPCResponse.CRLF_SEPARATOR \
                for i in range(len(chunked_elements) // 2)
        ]
        buf_size = min(DEFAULT_RECV_BUF_SIZE, target_chunk_content_length + len(RPCResponse.CRLF_SEPARATOR) - current_chunk_content_length)

        return complete_chunks, current_chunk, buf_size, response_completed


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

            if data.startswith(b'Content-Length:'):
                content_len = int(data[16:])

            if RPCResponse.is_chunked(response_data):
                chunked = True

        if response_data == b'':
            raise IOError

        if content_len > 0:
            data = fd.read(content_len)
            response_data += data
            callback(response_data)
        else:
            assert chunked, response_data
            callback(response_data)
            response_data = bytearray()

            while True:
                data = fd.readline(self.MAX_LINE_LEN + 1)
                chunk_len = int(data.decode("UTF-8"), 16)
                response_data += data

                data = fd.read(chunk_len + 2)  # +2 to read '/r/n'
                response_data += data

                callback(response_data)

                if chunk_len == 0:
                    break

                response_data = bytearray()

    def update_socket(self, sock: BaseSocket) -> None:
        self.rfile = sock.socket.makefile('rb', -1)
