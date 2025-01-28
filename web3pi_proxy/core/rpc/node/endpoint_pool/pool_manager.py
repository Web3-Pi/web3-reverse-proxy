from __future__ import annotations

import json
import select
import socket

import time
from threading import RLock, Thread
from typing import List, Tuple
from httptools import HttpResponseParser

from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3pi_proxy.core.rpc.node.endpoint_pool.load_balancers import (
    LoadBalancer,
)
from web3pi_proxy.core.rpc.node.endpoint_pool.tunnel_connection_pool import TunnelConnectionPool
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor, ConnectionType,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import (
    EndpointConnectionHandler,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.utils.logger import get_logger
from web3pi_proxy.config.conf import Config


class ConnectionPoolError(Exception):
    pass


class NoActivePoolsError(ConnectionPoolError):
    message = "No connection pools available"


class NoPoolPickedError(ConnectionPoolError):
    message = "Could not pick a connection pool"


class PoolDoesNotExistError(ConnectionPoolError):
    def __init__(self, name: str) -> None:
        self.message = f"No pool for endpoint {name} found"


class PoolAlreadyExistsError(ConnectionPoolError):
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
        self.__logger.debug(f"Connection pool: {pool}")
        self.__logger.debug(f"Failure rate: {failure_rate}")
        all_records = pool.stats.count_all(self.__INTERVAL_NS)
        self.__logger.debug(f"All records: {all_records}")
        return (
            all_records >= self.__MIN_CONNECTIONS
            and failure_rate >= self.__FAILURE_RATE_THRESHOLD
        )

    def __suspend_pool(self, pool) -> None:
        if not pool.is_active():
            return
        pool.disable()
        while True:
            time.sleep(self.__SUSPENSION_TIMEOUT_SECONDS)
            if pool.test_conn():
                pool.activate()
                break
            else:
                continue

    def check_connections(self, pools: List[EndpointConnectionPool]):
        for pool in pools:
            if self.__is_broken(pool):
                self.__logger.warning(
                    f"Endpoint `{pool.endpoint.name}`: connection failure rate excessive."
                )
                Thread(
                    target=self.__suspend_pool,
                    args=[pool],
                    daemon=True,
                ).start()

            self.__logger.debug(f"Endpoint `{pool.endpoint.name}`: okay.")


class SyncControllerResponseListener:
    body: bytes = b''
    block_number: int = 0
    block_timestamp: int = 0
    __logger = get_logger("SyncController")

    def __init__(self, __pool_name: str):
        self.__pool_name = __pool_name

    def on_status(self, status_code: int):
        self.__logger.debug(f"SyncControllerResponseListener.on_status: {status_code}")


    def on_body(self, body: bytes):
        self.body = self.body + body

    def on_message_complete(self):
        try:
            block_data = json.loads(self.body)
            result = block_data.get('result')
            if not result:
                error = block_data.get('error')
                self.__logger.error(f"{self.__pool_name}: Sync test failed: {error or 'reason unknown'}")
                return
            self.block_number = int(result['number'], 16)
            self.block_timestamp = int(result['timestamp'], 16)
        except Exception as error:
            self.__logger.error("%s: %s", error.__class__, error)
            self.__logger.error(f"{self.__pool_name}: Failed to parse sync test response")


# TODO: Tune parameters
class SyncController:
    __SUSPENSION_TIMEOUT_SECONDS = 60
    __MAX_DELAY_SECONDS = 60

    __logger = get_logger("SyncController")

    def __test_pool(self, pool: EndpointConnectionPool) -> bool | None:
        endpoint_connection_handler: EndpointConnectionHandler | None = None
        try:
            endpoint_connection_handler = pool.get(out_of_sync=True)
            req = RPCRequest()
            req.headers = b'Accept: */*\r\nContent-Type: application/json\r\nContent-Length: 82\r\n'
            req.content = b'{"method":"eth_getBlockByNumber","params":["latest",false],"id":1,"jsonrpc":"2.0"}'
            endpoint_connection_handler.send(req)

            response_listener = SyncControllerResponseListener(pool.endpoint.name)
            response_parser = HttpResponseParser(response_listener)

            def response_handler(res: bytes):
                nonlocal response_parser
                response_parser.feed_data(res)

            endpoint_connection_handler.receive(response_handler)

            current_timestamp = int(time.time())
            block_timestamp = response_listener.block_timestamp
            if block_timestamp == 0:
                return None  # no logs, failure already logged by the listener
            if block_timestamp + self.__MAX_DELAY_SECONDS > current_timestamp:
                return True
            else:
                self.__logger.warning(f"{pool.endpoint.name}: The node out of sync")
                return False
        except Exception as error:
            self.__logger.error("%s: %s", error.__class__, error)
            self.__logger.error(f"{pool.endpoint.name}: Failed to run sync test")
            return None
        finally:
            if endpoint_connection_handler:
                endpoint_connection_handler.release()  # safe: does not throw an exception

    def __suspend_pool(self, pool) -> None:
        if not pool.is_active():
            return
        pool.out_of_sync()
        while True:
            time.sleep(self.__SUSPENSION_TIMEOUT_SECONDS)
            test_result = self.__test_pool(pool)
            if test_result is not None and test_result:
                pool.activate()
                break
            else:
                continue

    def check_pools(self, pools: List[EndpointConnectionPool]):
        for pool in pools:
            test_result = self.__test_pool(pool)
            if test_result is not None and not test_result:
                self.__logger.warning(
                    f"Endpoint `{pool.endpoint.name}`: sync test: out of sync."
                )
                Thread(
                    target=self.__suspend_pool,
                    args=[pool],
                    daemon=True,
                ).start()

            self.__logger.debug(f"Endpoint `{pool.endpoint.name}`: sync test okay.")


class EndpointConnectionPoolManager:
    __DAMAGE_CONTROLLER_TIMEOUT_SECONDS = 10  # 600
    __SYNC_CONTROLLER_TIMEOUT_SECONDS = 60
    __logger = get_logger(f"EndpointConnectionPoolManager")

    def __init__(
        self,
        descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
        load_balancer: LoadBalancer,
    ):
        self.load_balancer = load_balancer
        self.damage_controller = DamageController()
        self.sync_controller = SyncController()
        self.pools: dict[str, EndpointConnectionPool] = {}
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

        self.sync_controller_thread = Thread(
            target=self.__sync_control,
            daemon=True,
        )
        self.sync_controller_thread.start()

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

    def __get_open_pools(self):
        return [
            connection_pool
            for connection_pool in self.pools.values()
            if connection_pool.is_open()
        ]

    def __damage_control(self):
        while True:
            self.__logger.debug("Running check on endpoint connections")
            with self.__lock:
                active_pools = self.__get_active_pools()
            self.damage_controller.check_connections(active_pools)
            time.sleep(self.__DAMAGE_CONTROLLER_TIMEOUT_SECONDS)

    def __sync_control(self):
        while True:
            self.__logger.debug("Running sync check on endpoint connections")
            with self.__lock:
                active_pools = self.__get_active_pools()
            self.sync_controller.check_pools(active_pools)
            time.sleep(self.__SYNC_CONTROLLER_TIMEOUT_SECONDS)

    def add_pool(
        self, name: str, conn_descr: EndpointConnectionDescriptor
    ) -> RPCEndpoint:
        with self.__lock:
            if name in self.pools.keys():
                raise PoolAlreadyExistsError(name)
            self.__logger.debug(
                f"Creating endpoint {name} with connection {conn_descr}"
            )
            endpoint = RPCEndpoint.create(name, conn_descr)
            if endpoint.conn_descr.connection_type == ConnectionType.TUNNEL:
                connection_pool = TunnelConnectionPool(endpoint)
            else:
                connection_pool = EndpointConnectionPool(endpoint)
            self.pools[name] = connection_pool
            return endpoint

    def remove_pool(self, name) -> RPCEndpoint:
        with self.__lock:
            connection_pool = self.pools.get(name)
            if connection_pool is None:
                raise PoolDoesNotExistError(name)
            endpoint = connection_pool.endpoint
            connection_pool.close()  # TODO this closes all connections and could be done in a separate thread
            del self.pools[name]
            return endpoint

    def get_pool(self, name: str) -> EndpointConnectionPool:
        with self.__lock:
            return self.pools.get(name)

    def get_connection(self, req: RPCRequest) -> EndpointConnectionHandler:
        self.__logger.debug("Selecting endpoint")
        with self.__lock:
            active_pools = self.__get_active_pools()
            if not active_pools:
                raise NoActivePoolsError()
            pool = self.load_balancer.pick_pool(req, active_pools)
            if pool is None:
                raise NoPoolPickedError()
        self.__logger.debug(f"Selected endpoint{pool.endpoint}")
        return pool.get()

    def close(self) -> None:
        with self.__lock:
            for connection_pool in self.pools.values():
                connection_pool.close()
