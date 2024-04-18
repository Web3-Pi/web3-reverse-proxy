from httptools import HttpRequestParser, HttpResponseParser

from core.rpc.request.rpcrequest import RPCRequest
from core.rpc.response.rpcresponse import RPCResponse
from core.sockets.basesocket import BaseSocket
from core.sockets.clientsocket import ClientSocket


class ParserTempResponse:

    def __init__(self) -> None:
        self.need_more_data_ = True

    def on_message_complete(self):
        self.need_more_data_ = False

    def need_more_data(self) -> bool:
        return self.need_more_data_


def recv_response(cs: BaseSocket) -> bytearray:
    pt = ParserTempResponse()
    parser = HttpResponseParser(pt)

    raw_resp = bytearray()
    while pt.need_more_data():
        data = cs.recv()
        if data is None or data == b'':
            raise IOError

        parser.feed_data(data)
        raw_resp += data

    return raw_resp
