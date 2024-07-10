from __future__ import annotations

import time
from typing import Set
from enum import Enum
from queue import SimpleQueue
from threading import Lock, RLock, Thread

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
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
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
        self.connection_close_queue: SimpleQueue[EndpointConnection | None] = SimpleQueue()

        self.closing_thread = Thread(
            target=self.__run_closing_thread,
            daemon=True,
        )
        self.closing_thread.start()

        self.cleanup_thread = Thread(
            target=self.__run_cleanup_thread,
            daemon=True,
        )
        self.cleanup_thread.start()

    def __str__(self):
        return f"{self.__class__.__name__}({self.endpoint})"

    class PoolStatus(Enum):
        ACTIVE = "ACTIVE"
        DISABLED = "DISABLED"
        CLOSING = "CLOSING"
        CLOSED = "CLOSED"

    def __run_closing_thread(self):
        while True:
            connection = self.connection_close_queue.get()
            if not connection:  # None is the sentinel
                break
            try:
                connection.close()
            except Exception as ex:
                self.__logger.error(f"Error while closing a connection", ex)

    def __run_cleanup_thread(self) -> None:
        while True:
            with self.__lock:
                if self.status == self.PoolStatus.CLOSED.value or self.status == self.PoolStatus.CLOSING.value:
                    break
                if self.status == self.PoolStatus.ACTIVE.value:
                    excessive_connections = self.connections.qsize() - self.MAX_CONNECTIONS
                    if excessive_connections > 0:
                        for _ in range(excessive_connections):
                            connection = self.__get_connection()  # no need to catch an error, guarded with the lock
                            self.connection_close_queue.put(connection)
                    obsolete_connections = 0
                    if self.connections.qsize() > 0:
                        validity_timestamp = time.time_ns() - Config.IDLE_CONNECTION_TIMEOUT * 1_000_000_000
                        for _ in range(self.connections.qsize()):  # this rotates the whole queue
                            connection = self.__get_connection()
                            if connection.last_use_timestamp < validity_timestamp:
                                obsolete_connections += 1
                                self.connection_close_queue.put(connection)
                            else:
                                self.connections.put(connection)
            if excessive_connections > 0:
                self.__logger.debug(f"Scheduled {excessive_connections} excessive connections for removal.")
            if obsolete_connections > 0:
                self.__logger.debug(f"Scheduled {obsolete_connections} obsolete connections for removal.")
            time.sleep(Config.IDLE_CONNECTION_TIMEOUT)

    def __get_connection(self) -> EndpointConnection:
        return self.connections.get_nowait()

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
            self.__logger.debug("No existing connections available, establishing new connection")
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
        with self.__lock:
            self.busy_connections.add(connection)
        return EndpointConnectionHandler(connection, self, is_new)

    def put(self, connection: EndpointConnection) -> None:
        self.__logger.debug(f"Putting connection {connection} to pool")
        with self.__lock:
            self.busy_connections.remove(connection)
            if self.is_active():
                self.stats.register_successful_connection()
                self.connections.put(connection)
                connection.last_use_timestamp = time.time_ns()
            else:
                self.connection_close_queue.put(connection)
                if self.status == self.PoolStatus.CLOSING.value:  # cant be CLOSED
                    if len(self.busy_connections) == 0:
                        self.connection_close_queue.put(None)  # sentinel
                        self.__update_status(self.PoolStatus.CLOSED.value)
                        self.__logger.info("Pool has been closed")

    def is_active(self):
        return self.status == self.PoolStatus.ACTIVE.value

    def disable(self):
        with self.__lock:
            if self.status == self.PoolStatus.CLOSED.value or self.status == self.PoolStatus.CLOSING.value:
                raise Exception("Tried to disable after close")  # TODO better exception
            self.__update_status(self.PoolStatus.DISABLED.value)
            while not self.connections.empty():
                self.connection_close_queue.put(self.__get_connection())
            self.stats = PoolStats()
        self.__logger.info("Pool has been disabled")

    def activate(self):
        with self.__lock:
            if self.status == self.PoolStatus.CLOSED.value or self.status == self.PoolStatus.CLOSING.value:
                raise Exception("Tried to activate after close")  # TODO better exception
            self.__update_status(self.PoolStatus.ACTIVE.value)
        self.__logger.info("Pool has been activated")

    def test_conn(self) -> bool:
        """Should not throw any exceptions.
        Always creates a new connection outside a pool and tests a node."""
        req = RPCRequest()
        req.content = \
            bytearray(b"{"
                      b"\"jsonrpc\":\"2.0\", "
                      b"\"method\":\"eth_getBlockByNumber\", "
                      b"\"params\":[\"latest\", false], "
                      b"\"id\":1"
                      b"}")
        req.headers = (
            bytearray(b"User-Agent: web3pi/proxy\r\n"
                      b"Accept: */*\r\n"
                      b"Content-Type: application/json\r\n"
                      b"Content-Length: 86\r\n"))

        valid_response = False

        def response_handler(res):
            nonlocal valid_response
            valid_response = valid_response or len(res) > 0  # TODO better response validation

        try:
            connection = EndpointConnection(self.endpoint)
        except Exception:
            return False

        try:
            connection.req_sender.send_request(req)
            connection.res_receiver.recv_response(response_handler)
        except Exception:
            return False
        finally:
            try:
                connection.close()
            except Exception:
                return False

        return valid_response

    def handle_broken_connection(self, connection: EndpointConnection, is_new=False):
        self.__logger.warning(f"Reported failure for connection {connection}")
        self.busy_connections.remove(connection)
        if is_new:
            self.stats.register_error_on_new_connection()
        else:
            self.stats.register_error_on_connection()
        self.connection_close_queue.put(connection)

    def close(self) -> None:
        with self.__lock:
            self.__update_status(self.PoolStatus.CLOSING.value)
            while not self.connections.empty():
                self.connection_close_queue.put(self.__get_connection())
            if len(self.busy_connections) == 0:
                self.connection_close_queue.put(None)  # sentinel
                self.__update_status(self.PoolStatus.CLOSED.value)
                self.__logger.info("Pool has been closed")
            else:
                self.__logger.info("Pool is closing")

