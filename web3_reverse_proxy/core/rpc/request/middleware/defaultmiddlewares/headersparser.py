from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


class ParseHeadersRequestReader(RequestReaderMiddleware):

    def __init__(self, next_reader: RequestReaderMiddleware):
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        try:
            content_len = -1
            no_headers = 0
            raw_headers_data = bytearray()

            fd = cs.get_read_fd()

            while True:
                data = fd.readline(self.MAX_LINE_LEN + 1)

                if len(data) > self.MAX_LINE_LEN:
                    return self.failure(ErrorResponses.payload_too_large(req.id), req)

                if data in (b'\r\n', b'\n', b''):
                    break

                if not data.startswith(b"Host:"):
                    raw_headers_data += data

                no_headers += 1
                if no_headers > self.MAX_NUM_HEADERS:
                    return self.failure(ErrorResponses.bad_request_headers(req.id), req)

                if data.startswith(b"Content-Length:"):
                    content_len = int(data[16:])

            if content_len < 0:
                return self.failure(ErrorResponses.bad_request_invalid_request_format(req.id), req)

            req.content_len = content_len
            req.headers = raw_headers_data

        except IOError:
            return self.failure()
        except Exception:
            raise

        return self.next_reader.read_request(cs, req)

    def __str__(self):
        return f"HeadersParser -> {self.next_reader}"
