from queue import Queue
from typing import Dict, Iterable

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.examples.endpointshandlers.threadsgraph.graphimpl import (
    Queues,
    ThreadsGraph,
)
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class MultiEndpointLocalLoadBalancingQoSHandler(EndpointsHandler):

    def __init__(
        self,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ) -> None:
        super().__init__()

        self.endpoint_0 = RPCEndpoint.create(name + " 0", conn_descr, state_updater)
        self.endpoint_1 = RPCEndpoint.create(name + " 1", conn_descr, state_updater)

        self.tg = ThreadsGraph()
        self.tg.add_processing_thread(
            self.request_consumer, Queues.IN_0, Queues.OUT_0, self.endpoint_0
        )
        self.tg.add_processing_thread(
            self.request_consumer, Queues.IN_1, Queues.OUT_0, self.endpoint_1
        )

        self.even_req_queue = self.tg.get_queue(Queues.IN_0)
        self.odd_req_queue = self.tg.get_queue(Queues.IN_1)

        self.res_queue = self.tg.get_queue(Queues.OUT_0)

        self.counter = {0: 0, 1: 0}

        self.counter_tracker = {}

        self.no_pending_requests = 0

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        if self.counter[1] > self.counter[0]:
            self.even_req_queue.put((cs, req))
            self.counter[0] += 1
            self.counter_tracker[cs] = 0
        else:
            self.odd_req_queue.put((cs, req))
            self.counter[1] += 1
            self.counter_tracker[cs] = 1

        self.no_pending_requests += 1

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        ret = {}
        while not self.res_queue.empty():
            cs, res = self.res_queue.get()
            ret[cs] = res

            self.no_pending_requests -= 1

            handled_by_endpoint_no = self.counter_tracker[cs]
            self.counter_tracker.pop(cs)

            self.counter[handled_by_endpoint_no] -= 1

        return ret

    @staticmethod
    def request_consumer(req_q: Queue, res_q: Queue, endpoint: RPCEndpoint) -> None:
        while True:
            cs, req = req_q.get()
            res = endpoint.handle_request_response_roundtrip(req)
            res_q.put((cs, res))

    def has_pending_requests(self) -> bool:
        return self.no_pending_requests > 0

    def close(self):
        self.endpoint_0.close()
        self.endpoint_1.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return [self.endpoint_0, self.endpoint_1]
