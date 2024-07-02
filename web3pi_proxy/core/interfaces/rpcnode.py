from abc import ABC, abstractmethod
from typing import Dict, Iterable

from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3pi_proxy.core.sockets.clientsocket import ClientSocket


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


class LoadBalancer(ABC):
    @abstractmethod
    def get_queue_for_request(
        self,
        endpoint_handler: EndpointsHandler,
        req: RPCRequest,
    ) -> int:
        pass
