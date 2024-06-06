from httptools import HttpRequestParser, HttpParserError

from web3_reverse_proxy.config.conf import Config
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.utils.logger import get_logger


class HttpRequestParserListener:

    def __init__(self, req: RPCRequest) -> None:
        self.req = req
        req.headers = b''
        self.need_more_data = True

    def on_url(self, url: bytes):
        self.req.user_api_key = str(url[1:], 'utf-8')  # TODO is it utf-8? TODO do we need str?

    def on_header(self, name: bytes, value: bytes):
        if name.lower() == b'host':
            pass
        elif name.lower() == b'connection':
            self.req.keep_alive = value != b'close'  # TODO is value already trimmed? TODO value is case sensitive?
        else:
            self.req.headers = self.req.headers + name + b': ' + value + b'\r\n'

    def on_body(self, body: bytes):
        self.req.content = body
        self.req.content_len = len(body)

    def on_message_complete(self):
        self.need_more_data = False


class RequestReader(RequestReaderMiddleware):
    __logger = get_logger("RequestReader")

    def __init__(self, next_reader: RequestReaderMiddleware = None):
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        buf_size = Config.DEFAULT_RECV_BUF_SIZE

        request_listener = HttpRequestParserListener(req)
        request_parser = HttpRequestParser(request_listener)

        try:
            while request_listener.need_more_data:
                assert cs.is_ready_read()
                data = cs.recv(buf_size)
                if not data:
                    raise IOError
                request_parser.feed_data(data)
        except HttpParserError as error:
            self.__logger.error(error)
            req.keep_alive = False
            return self.failure(ErrorResponses.http_bad_request(), req)
        except IOError:
            self.__logger.error("IOError")
            req.keep_alive = False
            return self.failure(bytes(), req)  # Empty response for closed connection

        if request_parser.get_method() != b"POST":
            return self.failure(ErrorResponses.http_method_not_allowed(), req)

        if req.content is None or req.content_len == 0 or len(req.content.strip()) == 0:
            return self.failure(ErrorResponses.http_bad_request(), req)

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

        return self.success(req)

    def __str__(self):
        if self.next_reader:
            return f"Content -> {self.next_reader}"
        else:
            return "Content"
