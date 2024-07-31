from __future__ import annotations

from abc import ABCMeta, abstractmethod
from random import randint
from typing import List

from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.utils.logger import get_logger

logger = get_logger(__name__)


class LoadBalancer(metaclass=ABCMeta):
    """Load Balancer interface."""

    @abstractmethod
    def pick_pool(self, req: RPCRequest, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool | None:
        """
        Choose one connection pool from passed active connection pools.
        The implementation cannot be blocking because of connection pools manager lock.
        """
        pass


class RandomLoadBalancer(LoadBalancer):
    """Picks a connection pool at random."""
    def pick_pool(self, req: RPCRequest, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        random_index = randint(0, len(pools) - 1)
        return pools[random_index]


class LeastBusyLoadBalancer(RandomLoadBalancer):
    """Picks one of the connection pools with the least utilization."""

    def pick_pool(self, req: RPCRequest, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool:
        pools_utilization = [(len(pool.busy_connections), pool) for pool in pools]
        min_utilization = min(pu[0] for pu in pools_utilization)
        chosen_pool = super().pick_pool(
            req,
            [pu[1] for pu in pools_utilization if pu[0] <= min_utilization]
        )
        logger.debug("Chosen pool: %s, min_utilization: %s", chosen_pool, min_utilization)
        return chosen_pool


class ConstantLoadBalancer(LoadBalancer):
    """Picks a connection pool constantly based on user configuration."""
    def pick_pool(self, req: RPCRequest, pools: List[EndpointConnectionPool]) -> EndpointConnectionPool | None:
        pool_name = req.constant_pool
        if pool_name is None:
            return None
        for pool in pools:
            if pool.endpoint.name == pool_name:
                return pool
        return None

