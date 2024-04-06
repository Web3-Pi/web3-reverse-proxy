import json

from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.validation.validators import \
    JSONRPCFormatValidator, JSONRPCContentValidator, JSONRPCMethodValidator
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.validation.errors import JSONRPCError

from web3_reverse_proxy.utils.logger import get_logger


class AcceptJSONRPCContentReader(RequestReaderMiddleware):
    VALIDATORS = [
        JSONRPCFormatValidator,
        JSONRPCContentValidator,
        JSONRPCMethodValidator,
    ]
    _logger = get_logger("AcceptJSONRPCContentReader")

    def __init__(self, next_reader: RequestReaderMiddleware = None) -> None:
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        jsonrpc_content = req.content

        try:
            json_content = json.loads(jsonrpc_content.decode("utf-8"))
        except:
            self._logger.error(f"Request {req} is incorrect JSON format")
            return self.failure(ErrorResponses.parse_error(req.id), req)

        try:
            for validator in self.VALIDATORS:
                validator.validate(json_content)
        except JSONRPCError as error:
            self._logger.error(f"Request {req} failed with {error}")
            return self.failure(ErrorResponses.bad_request_web3(error.code, error.message, req.id), req)
        except:
            self._logger.error(f"Internal error while parsing request {req}")
            return self.failure(ErrorResponses.internal_server_error(), req)

        req.method = json_content["method"]
        req.id = json_content["id"]

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

    def __str__(self):
        if self.next_reader:
            return f"AcceptRPCPayload -> {self.next_reader}"
        return "AcceptRPCPayload"
