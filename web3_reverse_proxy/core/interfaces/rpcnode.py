from abc import ABC, abstractmethod
from typing import Dict, Iterable

from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse

from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint


class EndpointsHandler(ABC):

    @abstractmethod
    def add_request(self, cs: ClientSocket, req: RPCRequest):
        pass

    @abstractmethod
    def has_pending_requests(self) -> bool:
        pass

    @abstractmethod
    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        pass
