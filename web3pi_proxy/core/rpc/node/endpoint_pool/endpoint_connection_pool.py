from __future__ import annotations

import time
from typing import Set
from enum import Enum
from queue import SimpleQueue
from threading import Lock, RLock

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.rpc.node.endpoint_pool.connection_pool import (
    ConnectionPool,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import (
    EndpointConnectionHandler,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import (
    EndpointConnection,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3pi_proxy.utils.logger import get_logger


# TODO: Remove old timestamps, if time-based checks are still applied
class PoolStats:
    def __init__(self) -> None:
        self.busy_connections = 0

        self.successful_connection_timestamps = []
        self.error_timestamps = []
        self.new_connection_error_timestamps = []
        self.connection_creation_error_timestamps = []
        self.__lock = RLock()

    def register_successful_connection(self) -> None:
        with self.__lock:
            self.successful_connection_timestamps.append(time.time_ns())

    def register_error_on_connection(self) -> None:
        with self.__lock:
            self.error_timestamps.append(time.time_ns())

    def register_error_on_new_connection(self) -> None:
        with self.__lock:
            self.new_connection_error_timestamps.append(time.time_ns())

    def register_error_on_connection_creation(self) -> None:
        with self.__lock:
            self.connection_creation_error_timestamps.append(time.time_ns())

    def __count_timestamps(self, timestamps: list[int], interval: int) -> int:
        threshold = time.time_ns() - interval
        with self.__lock:
            filtered_timestamps = [
                timestamp for timestamp in timestamps if timestamp >= threshold
            ]
        return len(filtered_timestamps)

    def count_successful_connections(self, interval: int) -> int:
        return self.__count_timestamps(self.successful_connection_timestamps, interval)

    def count_connection_errors(self, interval: int) -> int:
        return self.__count_timestamps(self.successful_connection_timestamps, interval)

    def count_new_connection_errors(self, interval: int) -> int:
        return self.__count_timestamps(self.successful_connection_timestamps, interval)

    def count_connection_creation_errors(self, interval: int) -> int:
        return self.__count_timestamps(
            self.connection_creation_error_timestamps, interval
        )

    def count_all_errors(self, interval: int) -> int:
        with self.__lock:
            all_errors = (
                self.error_timestamps
                + self.new_connection_error_timestamps
                + self.connection_creation_error_timestamps
            )
            return self.__count_timestamps(all_errors, interval)

    def count_all(self, interval: int) -> int:
        return self.count_all_errors(interval) + self.count_successful_connections(
            interval
        )

    def get_failure_rate(self, interval: int) -> float:
        error_count = self.count_all_errors(interval)
        all_connections = error_count + self.count_successful_connections(interval)
        return error_count / all_connections if all_connections > 0 else 0.0


class EndpointConnectionPool(ConnectionPool):
    MAX_CONNECTIONS = Config.NUM_PROXY_WORKERS

    def __init__(
        self,
        endpoint: RPCEndpoint,
    ):
        self.endpoint = endpoint
        self.connections: SimpleQueue[EndpointConnection] = SimpleQueue()
        self.busy_connections: Set[EndpointConnection] = set()
        self.stats = PoolStats()
        self.status = self.PoolStatus.ACTIVE.value
        self.__lock = Lock()
        self.__logger = get_logger(f"EndpointConnectionPool.{id(self)}")

    def __str__(self):
        return f"{self.__class__.__name__}({self.endpoint})"

    class PoolStatus(Enum):
        ACTIVE = "ACTIVE"
        DISABLED = "DISABLED"
        CLOSED = "CLOSED"

    def __cleanup(self) -> None:
        excessive_connections = self.connections.qsize() - self.MAX_CONNECTIONS
        if excessive_connections > 0:
            self.__logger.debug(
                f"Detected {excessive_connections} excessive connections"
            )
            for _ in range(excessive_connections):
                connection = self.__get_connection()
                self.__logger.debug(f"Removed connection {connection}")
                try:
                    connection.close()  # TODO: Move out of lock for better performance
                except OSError:
                    self.__logger.error(f"Failure on closing connection {connection}")

    def __get_connection(self) -> EndpointConnection:
        return self.connections.get_nowait()

    def __close(self) -> None:
        while not self.connections.empty():
            connection = self.__get_connection()
            try:
                connection.close()
            except OSError:
                self.__logger.error(f"Failure on closing connection {connection}")

    def __update_status(self, status: str):
        self.status = status
        self.__logger.debug(f"Changed status to {status}")

    def get(self) -> EndpointConnectionHandler:
        self.__lock.acquire()
        if not self.is_active():
            self.__lock.release()
            raise Exception("the pool is disabled")  # TODO better exception
        if self.connections.empty():
            self.__lock.release()
            self.__logger.debug(
                "No existing connections available, establishing new connection"
            )

            try:
                connection = EndpointConnection(self.endpoint)
            except Exception as error:
                self.stats.register_error_on_connection_creation()
                raise error

            is_new = True
        else:
            try:
                connection = self.__get_connection()
                is_new = False
            finally:
                self.__lock.release()

        self.__logger.debug(f"Return connection {connection}")
        self.busy_connections.add(connection)
        return EndpointConnectionHandler(connection, self, is_new)

    def put(self, connection: EndpointConnection) -> None:
        self.__logger.debug(f"Putting connection {connection} to pool")
        self.busy_connections.remove(connection)
        if self.is_active():
            self.stats.register_successful_connection()
            with self.__lock:
                self.connections.put(connection)
                self.__cleanup()
        else:
            self.__logger.warning(f"Connection returned on status {self.status}")
            self.__logger.debug(f"Shutting down connection {connection}")
            connection.close()

    def is_active(self):
        return self.status == self.PoolStatus.ACTIVE.value

    def disable(self):
        with self.__lock:
            self.__update_status(self.PoolStatus.DISABLED.value)
            self.__close()
            self.stats = PoolStats()
        self.__logger.info("Pool has been disabled")

    def activate(self):
        if self.status == self.PoolStatus.CLOSED.value:
            self.__logger.error("Tried to activate after closure")
        with self.__lock:
            self.__update_status(self.PoolStatus.ACTIVE.value)
        self.__logger.info("Pool has been activated")

    def handle_broken_connection(self, connection: EndpointConnection, is_new=False):
        self.__logger.warning(f"Reported failure for connection {connection}")
        self.busy_connections.remove(connection)
        if is_new:
            self.stats.register_error_on_new_connection()
        else:
            self.stats.register_error_on_connection()
        connection.close()

    def close(self) -> None:
        with self.__lock:
            self.__update_status(self.PoolStatus.CLOSED.value)
            self.__close()
