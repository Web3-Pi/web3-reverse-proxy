from __future__ import annotations

from typing import Dict, Iterable

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.examples.endpointshandlers.threadedhandlers.threadedendpointhandler import (
    ThreadedEndpointHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.threadsgraph.graphimpl import Queues
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class MultiInfuraArchEndpointHandler(ThreadedEndpointHandler):
    def __init__(
        self,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ):
        super().__init__()

        self.endpoint_non_arch = RPCEndpoint.create(
            name + " non-arch", conn_descr, state_updater
        )
        self.non_arch_responses = {}

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        if req.method != "eth_getBalance":
            self.non_arch_responses[cs] = (
                self.endpoint_non_arch.handle_request_response_roundtrip(req)
            )
            self.no_pending_requests += 1
        else:
            super().add_request(cs, req)

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        ret = self.non_arch_responses
        self.non_arch_responses = {}

        self.no_pending_requests -= len(ret)

        ret |= super().process_pending_requests()

        return ret

    def close(self) -> None:
        self.endpoint_non_arch.close()
        super().close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return [self.endpoint_non_arch] + list(super().get_endpoints())

    @classmethod
    def create(
        cls,
        name_geth: str,
        geth_descr: EndpointConnectionDescriptor,
        name_infura: str,
        infura_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ) -> MultiInfuraArchEndpointHandler:

        instance = MultiInfuraArchEndpointHandler(name_geth, geth_descr, state_updater)

        # # Endpoints are appended to the endpoints list in the order of adding consumers
        instance.add_request_consumer(
            Queues.IN_0,
            RPCEndpoint.create(name_infura + " arch", infura_descr, state_updater),
        )

        return instance
