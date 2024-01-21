from abc import ABC, abstractmethod

from web3_reverse_proxy.core.sockets.basesocket import BaseSocket
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class ResponseReceiver(ABC):

    @abstractmethod
    def recv_response(self) -> bytearray:
        pass

    @abstractmethod
    def update_socket(self, sock: BaseSocket) -> None:
        pass


class ResponseReceiverGeth(ResponseReceiver):

    def __init__(self, sock: BaseSocket) -> None:
        self.socket = sock

    def recv_response(self) -> bytearray:
        response_received = False
        raw_response = bytearray()

        while not response_received:
            assert self.socket.is_ready_read()

            data = self.socket.recv()
            raw_response += data

            # FIXME: this part requires a reliable approach
            response_received = RPCResponse.hack_is_complete_raw_response(raw_response)

        return raw_response

    def update_socket(self, sock: BaseSocket) -> None:
        self.socket = sock


class ResponseReceiverSSL(ResponseReceiver):

    MAX_LINE_LEN = 65536

    def __init__(self, sock: BaseSocket) -> None:
        self.rfile = sock.socket.makefile('rb', -1)

    # FIXME: this implementation is based on an assumption that the endpoint is a valid web3 endpoint (i.e. replies with
    #  valid responses only)
    def recv_response(self) -> bytearray:
        fd = self.rfile
        response_data = bytearray()

        data = fd.readline(self.MAX_LINE_LEN + 1)
        response_data += data
        content_len = -1
        chunked = False

        while True:
            data = fd.readline(self.MAX_LINE_LEN + 1)
            response_data += data

            if data in (b'\r\n', b'\n', b''):
                break

            if data.startswith(b'Content-Length:'):
                content_len = int(data[16:])

            if data == b'Transfer-Encoding: chunked\r\n':
                chunked = True

        if response_data == b'':
            raise IOError

        if content_len > 0:
            data = fd.read(content_len)
            response_data += data
        else:
            assert chunked, response_data

            while True:
                data = fd.readline(self.MAX_LINE_LEN + 1)
                chunk_len = int(data.decode("UTF-8"), 16)
                response_data += data

                data = fd.read(chunk_len + 2)  # +2 to read '/r/n'
                response_data += data

                if chunk_len == 0:
                    break

        return response_data

    def update_socket(self, sock: BaseSocket) -> None:
        self.rfile = sock.socket.makefile('rb', -1)
