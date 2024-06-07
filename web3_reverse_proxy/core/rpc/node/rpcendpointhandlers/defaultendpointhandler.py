from typing import Dict

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.singleendpointhandlerbase import (
    SingleEndpointHandlerBase,
)
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class SingleEndpointHandler(SingleEndpointHandlerBase):

    def __init__(
        self,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ) -> None:
        super().__init__(name, conn_descr, state_updater)

        self.responses = {}

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        self.responses[cs] = self.endpoint.handle_request_response_roundtrip(req)

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        res = self.responses
        self.responses = {}

        return res

    def has_pending_requests(self) -> bool:
        return len(self.responses) > 0
