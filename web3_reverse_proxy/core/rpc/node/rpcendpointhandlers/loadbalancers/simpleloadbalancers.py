import random

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest


class RandomLoadBalancer(LoadBalancer):
    @classmethod
    def get_queue_for_request(cls, endpoint_handler: EndpointsHandler, _req: RPCRequest) -> int:
        return random.randint(0, len(endpoint_handler.get_endpoints()) - 1)


class PriorityLoadBalancer(LoadBalancer):
    @classmethod
    def get_queue_for_request(cls, endpoint_handler: EndpointsHandler, req: RPCRequest) -> int:
        return min(len(endpoint_handler.get_endpoints()) - 1, req.priority)


class LeastBusyLoadBalancer(LoadBalancer):
    @classmethod
    def get_queue_for_request(cls, endpoint_handler: EndpointsHandler, _req: RPCRequest) -> int:
        return min(
            endpoint_handler.req_queues,
            key=lambda queue_id: endpoint_handler.req_queues.get(queue_id).qsize()
        )
