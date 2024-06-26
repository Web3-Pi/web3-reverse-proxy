from __future__ import annotations

from abc import ABCMeta, abstractmethod
from random import randint
from typing import List

from web3_reverse_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)


class LoadBalancer(metaclass=ABCMeta):
    @abstractmethod
    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        pass


class LeastBusyLoadBalancer(LoadBalancer):
    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        min_occupance = 10**10
        chosen_pool = None
        for pool in pools:
            occupance = pool.stats.free_connections * pool.stats.get_usage_rate()
            if occupance < min_occupance:
                min_occupance = occupance
                chosen_pool = pool
        return chosen_pool


class RandomLoadBalancer(LoadBalancer):
    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        random_index = randint(0, len(pools) - 1)
        return pools[random_index]
