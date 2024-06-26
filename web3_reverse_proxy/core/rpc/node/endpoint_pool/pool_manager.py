from __future__ import annotations

import time
from threading import RLock, Thread
from typing import List, Tuple

from web3_reverse_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3_reverse_proxy.core.rpc.node.endpoint_pool.load_balancers import (
    LoadBalancer,
    RandomLoadBalancer,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import (
    EndpointConnectionHandler,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.utils.logger import get_logger


class ConnectionPoolError(Exception):
    pass


class NoActivePoolsError(ConnectionPoolError):
    message = "No connection pools available"


class PoolDoesNotExist(ConnectionPoolError):
    def __init__(self, name: str) -> None:
        self.message = f"No pool for endpoint {name} found"


class PoolAlreadyExists(ConnectionPoolError):
    def __init__(self, name: str) -> None:
        self.message = f"No pool for endpoint {name} found"


# TODO: Consider triggering on each connection failure
# TODO: Tune parameters
class DamageController:
    __INTERVAL_NS = 60 * 10**9
    __MIN_CONNECTIONS = 10
    __FAILURE_RATE_THRESHOLD = 0.5
    __SUSPENSION_TIMEOUT_SECONDS = 10

    __logger = get_logger(f"DamageController")

    def __is_broken(self, pool: EndpointConnectionPool) -> bool:
        failure_rate = pool.stats.get_failure_rate(self.__INTERVAL_NS)
        self.__logger.debug(f"Conncetion pool: {pool}")
        self.__logger.debug(f"Failure rate: {failure_rate}")
        all_records = pool.stats.count_all(self.__INTERVAL_NS)
        self.__logger.debug(f"All records: {all_records}")
        return (
            all_records >= self.__MIN_CONNECTIONS
            and failure_rate >= self.__FAILURE_RATE_THRESHOLD
        )

    def __is_outdated(self, _pool: EndpointConnectionPool) -> bool:
        # TODO: Implement
        return False

    def __suspend_pool(self, pool) -> None:
        if pool.is_active():
            pool.disable()
            time.sleep(self.__SUSPENSION_TIMEOUT_SECONDS)
            pool.activate()

    def check_connections(self, pools: List[EndpointConnectionPool]):
        for pool in pools:
            if self.__is_broken(pool):
                self.__logger.warn(
                    f"Endpoint {pool.endpoint.name} has high connection failure rate"
                )
                Thread(
                    target=self.__suspend_pool,
                    args=[pool],
                    daemon=True,
                ).start()

            if self.__is_outdated(pool):
                self.__logger.warn(f"Endpoint {pool.endpoint.name} is falling behind")


class EndpointConnectionPoolManager:
    __DAMAGE_CONTROLLER_TIMEOUT_SECONDS = 10  # 600
    __logger = get_logger(f"EndpointConnectionPoolManager")

    def __init__(
        self,
        descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
        load_balancer: LoadBalancer = RandomLoadBalancer(),
    ):
        self.load_balancer = load_balancer
        self.damage_controller = DamageController()
        self.pools = {}
        self.__lock = RLock()

        for index in range(len(descriptors)):
            name, conn_descr = descriptors[index]
            assert conn_descr is not None
            self.add_pool(name, conn_descr)

        self.damage_controller_thread = Thread(
            target=self.__damage_control,
            daemon=True,
        )
        self.damage_controller_thread.start()

    @property
    def endpoints(self) -> List[RPCEndpoint]:
        with self.__lock:
            return [connection_pool.endpoint for connection_pool in self.pools.values()]

    def __get_active_pools(self):
        return [
            connection_pool
            for connection_pool in self.pools.values()
            if connection_pool.is_active()
        ]

    def __damage_control(self):
        while True:
            self.__logger.info("Running check on endpoint connections")
            self.damage_controller.check_connections(self.__get_active_pools())
            time.sleep(self.__DAMAGE_CONTROLLER_TIMEOUT_SECONDS)

    def add_pool(self, name: str, conn_descr: EndpointConnectionDescriptor) -> None:
        with self.__lock:
            if name in self.pools.keys():
                raise PoolAlreadyExists(name)
            self.__logger.debug(
                f"Creating endpoint {name} with connection {conn_descr}"
            )
            connection_pool = EndpointConnectionPool(
                RPCEndpoint.create(name, conn_descr)
            )
            self.pools[name] = connection_pool

    def remove_pool(self, name) -> RPCEndpoint:
        with self.__lock:
            connection_pool = self.pools.get(name)
            if connection_pool is None:
                raise PoolDoesNotExist(name)
            endpoint = connection_pool.endpoint
            connection_pool.close()
            del self.pools[name]
            return endpoint

    def get_connection(self) -> EndpointConnectionHandler:
        self.__logger.debug("Selecting endpoint")
        with self.__lock:
            pool = self.load_balancer.pick_pool(self.__get_active_pools())
            if pool is None:
                raise NoActivePoolsError()
            self.__logger.debug(f"Selected endpoint{pool.endpoint}")
            return pool.get()

    def close(self) -> None:
        with self.__lock:
            for connection_pool in self.pools.values():
                connection_pool.close()
