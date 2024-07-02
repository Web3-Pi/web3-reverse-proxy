from abc import ABC, abstractmethod

from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3pi_proxy.core.sockets.clientsocket import ClientSocket


class RequestReaderMiddleware(ABC):
    MAX_LINE_LEN = 65536
    MAX_NUM_HEADERS = 100

    ReturnType = [RPCRequest | None, RPCResponse | None]

    @staticmethod
    def failure(err_res: RPCResponse | bytes, req: RPCRequest) -> ReturnType:
        if isinstance(err_res, bytes):
            err_res = RPCResponse(bytearray(err_res), req)

        return None, err_res

    @staticmethod
    def success(req: RPCRequest) -> ReturnType:
        return req, None

    @abstractmethod
    def read_request(self, cs: ClientSocket, req: RPCRequest) -> ReturnType:
        """
        :param cs:
        :param req:
        :return: if success, then (RPCRequest, None),
        if error that is to be returned to client, then (None, RPCResponse),
        if fatal error and a connection should be dropped, then (None, None)
        """
        pass
