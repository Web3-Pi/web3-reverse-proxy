from web3_reverse_proxy.config.conf import JSON_RPC_REQUEST_PARSER_ENABLED

from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.validation.errors import MethodNotFoundError
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


class ContentRequestReader(RequestReaderMiddleware):

    def __init__(self, next_reader: RequestReaderMiddleware = None):
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        try:
            raw_content = cs.get_read_fd().read(req.content_len)

            # Windows curl fixup
            #  " - 123
            #  ' - 106
            if raw_content[0] == 123:
                raw_content = raw_content.replace(b"'", b'"')
                raw_content = raw_content.replace(b'"{', b"'{")
                raw_content = raw_content.replace(b'}"', b"}'")

            req.append_raw_data(raw_content)

            req.content = raw_content
        except IOError:
            return self.failure()
        except Exception:
            raise

        # TODO: Remove, once JSON parser is mandatory
        # the method needs to be read to keep track
        if not JSON_RPC_REQUEST_PARSER_ENABLED:
            method = None
            id = None
            for tok in raw_content.split(b","):
                if tok.startswith(b'"id":') or tok.startswith(b' "id":'):
                    id = str(tok.split(b":")[1][1:-1], 'utf-8').replace('"', '').strip()
                if tok.startswith(b'"method":') or tok.startswith(b' "method":'):
                    method = str(tok.split(b":")[1][1:-1], 'utf-8').replace('"', '').strip()

            if method is None:
                return self.failure(ErrorResponses.bad_request_web3(200, -32600, "Missing method field"), req)

            req.method = method
            req.id = id

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

        return self.success(req)

    def __str__(self):
        if self.next_reader:
            return f"Content -> {self.next_reader}"
        else:
            return "Content"
