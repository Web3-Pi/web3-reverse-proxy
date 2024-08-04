from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.sockets.basesocket import BaseSocket


class RequestSender:

    POST_REQUEST_LINE = "POST /{} HTTP/1.1\r\n"
    POST_REQUEST_LINE_1 = bytearray(b"POST ")
    POST_REQUEST_LINE_2 = bytearray(b" HTTP/1.1\r\n")
    HOST_LAST_HEADER = "Host: {}\r\n\r\n"

    def __init__(self, sock: BaseSocket, host: str, api_key: str = "") -> None:
        self.socket = sock

        self.url_context = bytearray(api_key.encode("UTF-8"))
        self.post_request_line = RequestSender.get_post_request_line(api_key)
        self.host_header_last = RequestSender.get_raw_host_last_header(host)

    def update_socket(self, sock: BaseSocket) -> None:
        self.socket = sock

    def send_request(self, req: RPCRequest) -> bytearray:
        req_data = req.as_bytearray(
            RequestSender.POST_REQUEST_LINE_1,
            self.url_context,
            RequestSender.POST_REQUEST_LINE_2,
            self.host_header_last
        )

        assert self.socket.is_ready_write()
        self.socket.send_all(req_data)

        return req_data

    @classmethod
    def get_raw_host_last_header(cls, host: str) -> bytearray:
        return bytearray(cls.HOST_LAST_HEADER.format(host).encode("UTF-8"))

    @classmethod
    def get_post_request_line(cls, api_key: str = "") -> bytearray:
        return bytearray(cls.POST_REQUEST_LINE.format(api_key).encode("UTF-8"))
