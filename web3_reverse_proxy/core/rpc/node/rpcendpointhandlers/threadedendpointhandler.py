from __future__ import annotations

from queue import Queue
from typing import Iterable, Callable, List, Tuple

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.threadsgraph.graphimpl import ThreadsGraph, Queues
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket

from web3_reverse_proxy.interfaces.servicestate import StateUpdater
from web3_reverse_proxy.utils.logger import get_logger


class ThreadedEndpointHandler(EndpointsHandler):
    _logger = get_logger("ThreadedEndpointHandler")

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
        self._logger.debug(f"Adding request {req} for {cs}")
        in_queue_index = self.load_balancer.get_queue_for_request(self, req)

        self.req_queues[in_queue_index].put((cs, req))
        self.no_pending_requests += 1
        self._logger.debug(f"Added request with {self.no_pending_requests} pending requests")

    def process_pending_requests(self) -> List[Tuple[ClientSocket, RPCResponse]]:
        ret = []
        while not self.res_queue.empty():
            cs, res = self.res_queue.get()
            ret.append((cs, res))

            if res.chunked:
                cs, res = self.res_queue.get()  # to omit header chunk
                ret.append((cs, res))
                while not RPCResponse.is_complete_raw_response(res.raw):
                    cs, res = self.res_queue.get()
                    ret.append((cs, res))

            self.no_pending_requests -= 1
        return ret

    @classmethod
    def request_consumer(cls, req_q: Queue, res_q: Queue, endpoint: RPCEndpoint) -> None:
        cls._logger.debug("Started consuming request")
        while True:
            cls._logger.debug(f"Endpoint {endpoint} awaiting requests...")
            cs, req = req_q.get()

            cls._logger.debug(f"Endpoint {endpoint} accepted request {req} from client socket {cs}")
            response_handler = lambda res: res_q.put((cs, res))

            cls._logger.debug("Initiating request/response roundtrip")
            endpoint.handle_request_response_roundtrip(req, response_handler)
            cls._logger.debug("Request/response roundtrip ended")

    def has_pending_requests(self) -> bool:
        return self.no_pending_requests > 0

    def close(self) -> None:
        for endpoint in self.endpoints:
            self._logger.debug(f"Closing endpoint {endpoint}")
            endpoint.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return self.endpoints
