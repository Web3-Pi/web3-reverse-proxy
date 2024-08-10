from httptools import HttpParserError, HttpRequestParser

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.sockets.clientsocket import ClientSocket
from web3pi_proxy.core.utilhttp.errors import ErrorResponses
from web3pi_proxy.utils.logger import get_logger


class HttpRequestParserListener:

    def __init__(self, req: RPCRequest) -> None:
        self.req = req
        req.headers = b""
        self.need_more_data = True

    def on_url(self, url: bytes):
        if len(url) < 2:  # empty or /
            self.req.user_api_key = None
        else:
            i = url.find(b'/', 1)
            if i > 0:
                self.req.user_api_key = str(
                    url[1:i], "utf-8"
                )  # TODO is it utf-8? TODO do we need str?
                self.req.url_path = url[i+1:]
            else:
                self.req.user_api_key = str(
                    url[1:], "utf-8"
                )  # TODO is it utf-8? TODO do we need str?

    def on_header(self, name: bytes, value: bytes):
        name_lower = name.lower()
        if name_lower == b"host":
            pass
        elif name_lower == b"connection":
            self.req.keep_alive = (
                value != b"close"
            )  # TODO is value already trimmed? TODO value is case sensitive?
        elif name_lower == b"origin":
            self.req.cors_origin = value
        else:
            self.req.headers = self.req.headers + name + b": " + value + b"\r\n"

    def on_body(self, body: bytes):
        self.req.content = body
        self.req.content_len = len(body)

    def on_message_complete(self):
        self.need_more_data = False


class RequestReader(RequestReaderMiddleware):
    __logger = get_logger("RequestReader")

    def __init__(self, next_reader: RequestReaderMiddleware = None):
        self.next_reader = next_reader

    def read_request(
        self, cs: ClientSocket, req: RPCRequest
    ) -> RequestReaderMiddleware.ReturnType:
        buf_size = Config.DEFAULT_RECV_BUF_SIZE

        request_listener = HttpRequestParserListener(req)
        request_parser = HttpRequestParser(request_listener)

        try:
            while request_listener.need_more_data:
                if not cs.is_ready_read(
                    timeout=0.1
                ):  # TODO total timeout for request reading, TODO parametrization
                    self.__logger.warning("client socket read timeout")
                    req.keep_alive = False  # just in case
                    return None, None
                data = cs.recv(buf_size)
                if not data:
                    self.__logger.debug("client socket closed")
                    req.keep_alive = False  # just in case
                    return None, None
                request_parser.feed_data(data)
        except HttpParserError as error:
            self.__logger.error(error)
            req.keep_alive = False
            return self.failure(ErrorResponses.http_bad_request(), req)
        except IOError:
            self.__logger.error("IOError")
            req.keep_alive = False
            return None, None

        req.http_method = request_parser.get_method()

        if req.http_method == b"POST":
            if req.content is None or req.content_len == 0 or len(req.content.strip()) == 0:
                return self.failure(ErrorResponses.http_bad_request(), req)
        elif req.http_method == b"OPTIONS":
            return self.success(req)
        else:
            return self.failure(ErrorResponses.http_method_not_allowed(), req)

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

        return self.success(req)

    def __str__(self):
        if self.next_reader:
            return f"Content -> {self.next_reader}"
        else:
            return "Content"
