from abc import ABC, abstractmethod

from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class StateUpdater(ABC):
    @abstractmethod
    def record_rpc_request(self, request: RPCRequest) -> None:
        pass

    @abstractmethod
    def record_rpc_response(self, request: RPCRequest, response: bytearray) -> None:
        pass
