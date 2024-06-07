from __future__ import annotations

from queue import Queue

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.examples.endpointshandlers.threadedhandlers.threadedendpointhandler import (
    ThreadedEndpointHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.threadsgraph.graphimpl import Queues
from web3_reverse_proxy.examples.helpers.ratelimiter import RateLimiter
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class PriorityEndpointHandler(ThreadedEndpointHandler):

    def __init__(self):
        super().__init__()

    def add_rate_limited_forwarder(
        self, queue_in: int, queue_out: int, max_rate: float
    ):
        self.add_processing_thread(
            self.rate_limited_request_forwarder, queue_in, queue_out, max_rate
        )

    def get_queue_for_request(self, req: RPCRequest) -> int:
        return super().get_queue_for_request(req)

    @staticmethod
    def rate_limited_request_forwarder(
        in_req_q: Queue, out_req_q: Queue, max_rate: float
    ) -> None:
        rate_limiter = RateLimiter(max_rate)

        while True:
            req_entry = in_req_q.get()
            rate_limiter.wait()
            out_req_q.put(req_entry)

    @classmethod
    def create_single_local_prio(
        cls,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
        max_rate_1: float,
        max_rate_2: float,
    ) -> PriorityEndpointHandler:

        instance = PriorityEndpointHandler()

        # Endpoints are appended to the endpoints list in the order of adding consumers
        instance.add_request_consumer(
            Queues.IN_0, RPCEndpoint.create(name, conn_descr, state_updater)
        )

        instance.add_rate_limited_forwarder(Queues.IN_1, Queues.IN_0, max_rate_1)
        instance.add_rate_limited_forwarder(Queues.IN_2, Queues.IN_0, max_rate_2)

        return instance

    @classmethod
    def create_multi_infura_prio(
        cls,
        name_eth: str,
        descr_eth: EndpointConnectionDescriptor,
        name_infura: str,
        descr_inf: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
        max_rate_1: float,
        max_rate_2: float,
    ) -> PriorityEndpointHandler:

        instance = PriorityEndpointHandler()

        # Endpoints are appended to the endpoints list in the order of adding consumers
        instance.add_request_consumer(
            Queues.IN_0, RPCEndpoint.create(name_eth + " 0,1", descr_eth, state_updater)
        )
        instance.add_request_consumer(
            Queues.IN_3,
            RPCEndpoint.create(name_infura + " 2", descr_inf, state_updater),
        )

        instance.add_rate_limited_forwarder(Queues.IN_1, Queues.IN_0, max_rate_1)
        instance.add_rate_limited_forwarder(Queues.IN_2, Queues.IN_3, max_rate_2)

        return instance
