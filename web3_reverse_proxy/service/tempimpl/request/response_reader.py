from httptools import HttpRequestParser, HttpResponseParser

from core.rpc.request.rpcrequest import RPCRequest
from core.rpc.response.rpcresponse import RPCResponse
from core.sockets.basesocket import BaseSocket
from core.sockets.clientsocket import ClientSocket


class ParserTempResponse:

    def __init__(self) -> None:
        self.raw_response: bytearray = bytearray()
        self.need_more_data_ = True

    def get_response(self) -> bytearray:
        return self.raw_response

    def on_message_begin(self):
        self.method_known = True
        # print("On Mesg Begin")

    def on_url(self, url: bytes):
        print(url)
        self.raw_response += url

    def on_header(self, name: bytes, value: bytes):
        self.raw_response += name + b': ' + value + b'\r\n'

    def on_status(self, status: bytes):
        if status == b'OK':
            self.raw_response += b'HTTP/1.1 200 OK\r\n'
        else:
            assert False

    def on_body(self, body: bytes):
        self.raw_response += body

    def on_message_complete(self):
        self.need_more_data_ = False

    def need_more_data(self) -> bool:
        return self.need_more_data_


def recv_response(cs: BaseSocket) -> bytearray | None:
    pt = ParserTempResponse()
    parser = HttpResponseParser(pt)

    while pt.need_more_data():
        data = cs.recv()
        if data is None or data == b'':
            raise IOError

        # print(data)
        parser.feed_data(data)

    return pt.get_response()
