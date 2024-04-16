from httptools import HttpRequestParser

from core.rpc.request.rpcrequest import RPCRequest
from core.rpc.response.rpcresponse import RPCResponse
from core.sockets.clientsocket import ClientSocket


class ParserTemp:

    def __init__(self) -> None:
        self.req = RPCRequest()

        self.headers_raw = bytearray()
        self.method_known = False
        self.need_more_data_ = True

    def get_request(self) -> RPCRequest:
        return self.req

    def on_message_begin(self):
        self.method_known = True
        # print("On Mesg Begin")

    def on_url(self, url: bytes):
        api_key = ''
        url = url.decode("utf-8")
        if len(url) > 1:
            api_key = url[1:]

        self.req.user_api_key = api_key
        # print(f"On URL {url}")
        # print(f"On URL {api_key}")

    def on_header(self, name: bytes, value: bytes):
        # print(f"On Header {name}: {value}")

        if name != b'Host':
            self.headers_raw += name + b': ' + value + b'\r\n'

            if name == b'Content-Length':
                self.req.content_len = int(value)
                # print(self.req.content_len)

    def on_headers_complete(self):
        # print(f"On Headers complete")
        self.req.headers = self.headers_raw

    def on_body(self, body: bytes):
        # print(f"On Body {body}, {len(body)}")

        method = None
        id = None
        for tok in body.split(b","):
            if tok.startswith(b'"id":') or tok.startswith(b' "id":'):
                id = str(tok.split(b":")[1][1:-1], 'utf-8').replace('"', '').strip()
            if tok.startswith(b'"method":') or tok.startswith(b' "method":'):
                method = str(tok.split(b":")[1][1:-1], 'utf-8').replace('"', '').strip()

        # print(id)
        # print(method)
        self.req.method = method
        self.req.id = id
        self.req.content = body

    def on_message_complete(self):
        self.need_more_data_ = False
        # print(self.req)
        # print(f"On Message Complete")

    def on_chunk_header(self):
        print(f"On Chunk Header")

    def on_chunk_complete(self):
        print(f"On Chunk Complete")

    def on_status(self, status: bytes):
        print(f"On Status {status}")

    def need_more_data(self) -> bool:
        return self.need_more_data_


class RequestReaderTemp:

    def __init__(self):
        pass

    def read_request(self, cs: ClientSocket) -> [RPCRequest | None, RPCResponse | None]:
        pt = ParserTemp()
        parser = HttpRequestParser(pt)

        while pt.need_more_data():
            data = cs.recv()
            if data is None or data == b'':
                return None, None

            # print(data)
            parser.feed_data(data)

        return pt.get_request(), None
