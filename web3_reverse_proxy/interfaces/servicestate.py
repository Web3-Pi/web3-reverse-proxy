from abc import ABC, abstractmethod

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest


class StateUpdater(ABC):
    @abstractmethod
    def record_rpc_request(self, request: RPCRequest) -> None:
        pass

    @abstractmethod
    def record_rpc_response(self, response: bytearray) -> None:
        pass
