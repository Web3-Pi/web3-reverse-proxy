from abc import ABC, abstractmethod

from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class RequestReaderMiddleware(ABC):
    MAX_LINE_LEN = 65536
    MAX_NUM_HEADERS = 100

    ReturnType = [RPCRequest | None, RPCResponse | None]

    @staticmethod
    def failure(err_res: RPCResponse | bytes | None = None, req: RPCRequest | None = None) -> ReturnType:
        if isinstance(err_res, bytes):
            assert req is not None
            err_res = RPCResponse(bytearray(err_res), req)

        return None, err_res

    @staticmethod
    def success(req: RPCRequest) -> ReturnType:
        return req, None

    @abstractmethod
    def read_request(self, cs: ClientSocket, req: RPCRequest) -> ReturnType:
        pass
