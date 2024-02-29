from __future__ import annotations

from queue import Queue
from typing import Dict, Iterable, Callable, List, Tuple

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.threadsgraph.graphimpl import ThreadsGraph, Queues
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket

from web3_reverse_proxy.interfaces.servicestate import StateUpdater



class ThreadedEndpointHandler(EndpointsHandler):

    def __init__(
            self,
            descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
            state_updater: StateUpdater,
            load_balancer: LoadBalancer,
        ):
        self.tg = ThreadsGraph()
        self.queues_ids = Queues.create(len(descriptors), 1)
        self.req_queues = {}
        self.res_queue = self.tg.get_queue(self.queues_ids.OUT_0)
        self.no_pending_requests = 0
        self.endpoints = []
        self.load_balancer = load_balancer

        for index in range(len(descriptors)):
            name, conn_descr = descriptors[index]
            assert conn_descr is not None
            self.add_request_consumer(self.queues_ids[index], RPCEndpoint.create(name, conn_descr, state_updater))

    def add_processing_thread(self, fun: Callable, queue_in: int, queue_out: int, *args):
        assert queue_in not in self.req_queues
        self.req_queues[queue_in] = self.tg.get_queue(queue_in)

        self.tg.add_processing_thread(fun, queue_in, queue_out, *args)

    def add_request_consumer(self, queue_in: int, endpoint: RPCEndpoint):
        if endpoint not in self.endpoints:
            self.endpoints.append(endpoint)

        self.add_processing_thread(self.request_consumer, queue_in, self.queues_ids.OUT_0, endpoint)

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        in_queue_index = self.load_balancer.get_queue_for_request(self, req)

        self.req_queues[in_queue_index].put((cs, req))
        self.no_pending_requests += 1

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        ret = {}

        while not self.res_queue.empty():
            cs, res = self.res_queue.get()
            ret[cs] = res

            self.no_pending_requests -= 1

        return ret

    @staticmethod
    def request_consumer(req_q: Queue, res_q: Queue, endpoint: RPCEndpoint) -> None:
        while True:
            cs, req = req_q.get()
            res = endpoint.handle_request_response_roundtrip(req)
            res_q.put((cs, res))

    def has_pending_requests(self) -> bool:
        return self.no_pending_requests > 0

    def close(self) -> None:
        for endpoint in self.endpoints:
            endpoint.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return self.endpoints
