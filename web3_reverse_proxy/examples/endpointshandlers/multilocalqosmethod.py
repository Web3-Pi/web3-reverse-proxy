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


class MultiEndpointLocalMethodQoSHandler(EndpointsHandler):

    def __init__(
        self,
        name: str,
        conn_descr: EndpointConnectionDescriptor,
        state_updater: StateUpdater,
    ) -> None:
        super().__init__()

        self.endpoint_fast = RPCEndpoint.create(name + " 1", conn_descr, state_updater)
        self.endpoint_diff = RPCEndpoint.create(name + " 2", conn_descr, state_updater)

        self.tg = ThreadsGraph()
        self.tg.add_processing_thread(
            self.request_consumer_diff, Queues.IN_0, Queues.OUT_0
        )

        self.diff_req_queue = self.tg.get_queue(Queues.IN_0)
        self.diff_res_queue = self.tg.get_queue(Queues.OUT_0)

        self.fast_responses = {}
        self.no_pending_requests = 0

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        if req.method == "eth_getBlockByNumber":
            self.diff_req_queue.put((cs, req))
        else:
            self.fast_responses[cs] = (
                self.endpoint_fast.handle_request_response_roundtrip(req)
            )

        self.no_pending_requests += 1

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        ret = self.fast_responses
        self.fast_responses = {}

        self.no_pending_requests -= len(ret)

        while not self.diff_res_queue.empty():
            cs, res = self.diff_res_queue.get()
            ret[cs] = res

            self.no_pending_requests -= 1

        return ret

    def request_consumer_diff(self, req_q: Queue, res_q: Queue) -> None:
        endpoint = self.endpoint_diff

        while True:
            cs, req = req_q.get()
            res = endpoint.handle_request_response_roundtrip(req)
            res_q.put((cs, res))

    def has_pending_requests(self) -> bool:
        return self.no_pending_requests > 0

    def close(self):
        self.endpoint_fast.close()
        self.endpoint_diff.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return [self.endpoint_fast, self.endpoint_diff]
