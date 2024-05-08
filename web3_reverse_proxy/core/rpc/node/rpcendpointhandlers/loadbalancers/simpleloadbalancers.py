import random

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest


class RandomLoadBalancer(LoadBalancer):
    @classmethod
    def get_queue_for_request(cls, endpoints: list, _req: RPCRequest) -> int:
        return random.randint(0, len(endpoints) - 1)


class PriorityLoadBalancer(LoadBalancer):
    @classmethod
    def get_queue_for_request(cls, endpoints: list, req: RPCRequest) -> int:
        return min(len(endpoints) - 1, req.priority)
