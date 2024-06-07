from email.utils import formatdate
from queue import Queue
from typing import Dict, Iterable, List, Tuple

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


class MultiDeviceLocalLoadBalancingQoSHandler(EndpointsHandler):

    RES_CID_0 = bytearray(
        b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: "
    )
    RES_CID_1 = bytearray(
        b"\r\nContent-Length: 64\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2\xa80T\xaa\xe5\x02\x04\x00\x00\xff\xff\xe1\xb1\x0cF(\x00\x00\x00"
    )

    def __init__(
        self,
        descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
        updater: StateUpdater,
    ) -> None:
        super().__init__()

        assert len(descriptors) <= Queues.OUT_0

        self.endpoints = [
            RPCEndpoint.create(name, conn_descr, updater)
            for name, conn_descr in descriptors
        ]

        self.tg = ThreadsGraph()
        self.queues = []
        self.counter = {}
        for queue_in_no, endpoint in enumerate(self.endpoints):
            self.tg.add_processing_thread(
                self.request_consumer, queue_in_no, Queues.OUT_0, endpoint
            )
            self.queues.append(self.tg.get_queue(queue_in_no))
            self.counter[queue_in_no] = 0

        self.res_queue = self.tg.get_queue(Queues.OUT_0)

        self.counter_tracker = {}

        self.chain_id_responses = {}
        self.no_pending_requests = 0

    @classmethod
    def get_chain_id_response(cls, req: RPCRequest) -> RPCResponse:
        date = formatdate(timeval=None, localtime=False, usegmt=True).encode("utf-8")
        return RPCResponse(cls.RES_CID_0 + date + cls.RES_CID_1, req)

    def add_request(self, cs: ClientSocket, req: RPCRequest) -> None:
        if req.method == "eth_chainId":
            res = self.get_chain_id_response(req)
            self.chain_id_responses[cs] = res
        else:
            best_candidate_queue = min(self.counter, key=self.counter.get)

            self.queues[best_candidate_queue].put((cs, req))
            self.counter[best_candidate_queue] += 1
            self.counter_tracker[cs] = best_candidate_queue

        self.no_pending_requests += 1

    def process_pending_requests(self) -> Dict[ClientSocket, RPCResponse]:
        self.no_pending_requests -= len(self.chain_id_responses)

        ret = self.chain_id_responses
        while not self.res_queue.empty():
            cs, res = self.res_queue.get()
            ret[cs] = res

            self.no_pending_requests -= 1

            handled_by_endpoint_no = self.counter_tracker[cs]
            self.counter_tracker.pop(cs)

            self.counter[handled_by_endpoint_no] -= 1

        self.chain_id_responses = {}

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
        for endpoint in self.endpoints:
            endpoint.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return self.endpoints
