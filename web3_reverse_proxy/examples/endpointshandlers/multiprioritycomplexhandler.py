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


class MultiPriorityComplexEndpointHandler(ThreadedEndpointHandler):
    def __init__(
        self,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ):
        super().__init__()

        self.endpoint_fast = RPCEndpoint.create(
            name + " f-0", conn_descr, state_updater
        )
        self.fast_responses = {}

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        if req.priority == 0 and req.method == "net_version":
            self.fast_responses[cs] = (
                self.endpoint_fast.handle_request_response_roundtrip(req)
            )
            self.no_pending_requests += 1
        else:
            super().add_request(cs, req)

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        ret = self.fast_responses
        self.fast_responses = {}

        self.no_pending_requests -= len(ret)

        ret |= super().process_pending_requests()

        return ret

    def close(self) -> None:
        self.endpoint_fast.close()
        super().close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return [self.endpoint_fast] + list(super().get_endpoints())

    @classmethod
    def create(
        cls,
        name_geth: str,
        geth_descr: EndpointConnectionDescriptor,
        name_infura: str,
        infura_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ) -> MultiPriorityComplexEndpointHandler:

        instance = MultiPriorityComplexEndpointHandler(
            name_geth, geth_descr, state_updater
        )

        # # Endpoints are appended to the endpoints list in the order of adding consumers
        instance.add_request_consumer(
            Queues.IN_0,
            RPCEndpoint.create(name_geth + " s-0", geth_descr, state_updater),
        )
        instance.add_request_consumer(
            Queues.IN_1,
            RPCEndpoint.create(name_geth + " pt-1", geth_descr, state_updater),
        )
        instance.add_request_consumer(
            Queues.IN_2,
            RPCEndpoint.create(name_infura + " pt-2", infura_descr, state_updater),
        )

        return instance
