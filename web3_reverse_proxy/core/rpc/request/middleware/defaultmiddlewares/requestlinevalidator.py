from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


class AcceptRequestLineReader(RequestReaderMiddleware):

    def __init__(self, next_reader: RequestReaderMiddleware = None):
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        try:
            data = cs.get_read_fd().readline(self.MAX_LINE_LEN + 1)

            if len(data) == 0:
                return self.failure()

            if len(data) > self.MAX_LINE_LEN:
                return self.failure(ErrorResponses.bad_request_invalid_request_format())

            header = str(data, 'utf-8')
            words = header.split()

            if len(words) != 3 or words[0] != "POST":
                return self.failure(ErrorResponses.bad_request_invalid_request_format())

            req.user_api_key = words[1][1:].strip()
        except IOError:
            return self.failure()
        except Exception:
            raise

        return self.next_reader.read_request(cs, req)

    def __str__(self):
        return f"AcceptRequestLine -> {self.next_reader}"
