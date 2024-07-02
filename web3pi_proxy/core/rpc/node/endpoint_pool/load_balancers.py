from __future__ import annotations

from abc import ABCMeta, abstractmethod
from random import randint
from typing import List

from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3_reverse_proxy.utils.logger import get_logger

logger = get_logger(__name__)


class LoadBalancer(metaclass=ABCMeta):
    """Load Balancer interface."""

    @abstractmethod
    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        pass


class RandomLoadBalancer(LoadBalancer):
    """Picks a connection pool at random."""
    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        random_index = randint(0, len(pools) - 1)
        return pools[random_index]


class LeastBusyLoadBalancer(RandomLoadBalancer):
    """Picks one of the connection pools with the least utilization."""

    def pick_pool(self, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        pools_utilization = [(len(pool.busy_connections), pool) for pool in pools]
        min_utilization = min(pu[0] for pu in pools_utilization)
        chosen_pool = super().pick_pool(
            [pu[1] for pu in pools_utilization if pu[0] <= min_utilization]
        )
        logger.debug("Chosen pool: %s, min_utilization: %s", chosen_pool, min_utilization)
        return chosen_pool
