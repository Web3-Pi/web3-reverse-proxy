from __future__ import annotations

from queue import SimpleQueue
from typing import List, Tuple
from threading import Lock

from web3_reverse_proxy.config.conf import Config

from web3_reverse_proxy.core.interfaces.rpcnode import LoadBalancer
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.loadbalancers.simpleloadbalancers import RandomLoadBalancer
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import EndpointConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool

from web3_reverse_proxy.interfaces.servicestate import StateUpdater
from web3_reverse_proxy.utils.logger import get_logger


class EndpointConnectionPool(ConnectionPool):
    _logger = get_logger("EndpointConnectionPool")
    MAX_CONNECTIONS = Config.NUM_PROXY_WORKERS

    def __init__(
            self,
            descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
            state_updater: StateUpdater,
            load_balancer: LoadBalancer = RandomLoadBalancer,  # For convenience during architecture change
        ):
        self.endpoints = []
        self.load_balancer = load_balancer
        self.connections = SimpleQueue()
        self.lock = Lock()

        for index in range(len(descriptors)):
            name, conn_descr = descriptors[index]
            assert conn_descr is not None
            self._logger.debug(f"Creating endpoint {name} with connection {conn_descr}")
            self.endpoints.append(RPCEndpoint.create(name, conn_descr, state_updater))

    def _cleanup(self) -> None:
        excessive_connections = self.connections.qsize() - self.MAX_CONNECTIONS
        if excessive_connections > 0:
            self._logger.debug(f"Detected {excessive_connections} excessive connections")
            for _ in range(excessive_connections):
                connection = self.connections.get_nowait()
                self._logger.debug(f"Removed connection {connection}")
                try:
                    connection.close()
                except OSError:
                    self._logger.error(f"Failure on closing connection {connection}")

    def get(self) -> EndpointConnectionHandler:
        self._logger.debug("Selecting endpoint connection from pool")

        self.lock.acquire()
        if self.connections.empty():
            try:
                self._logger.debug("No existing connections available, establishing new connection")
                # TODO: Reconsider load balancers after new architecture is settled
                # TODO: Could be released sooner, if endpoints remain constant
                endpoint_index = self.load_balancer.get_queue_for_request(self.endpoints, RPCRequest())
            finally:
                self.lock.release()

            connection = self.endpoints[endpoint_index].create_connection()
        else:
            try:
                connection = self.connections.get_nowait()
            finally:
                self.lock.release()

        self._logger.debug(f"Return connection {connection}")
        return EndpointConnectionHandler(connection, self)

    def put(self, connection: EndpointConnection) -> None:
        self._logger.debug(f"Putting connection {connection} to pool")
        with self.lock:
            self.connections.put(connection)
            self._cleanup()

    # Intended for cleaning after shutdown
    def close(self) -> None:
        with self.lock:
            while not self.connections.empty():
                connection = self.connections.get_nowait()
                try:
                    connection.close()
                except OSError as error:
                    self._logger.error(f"Failure on closing connection {connection}")
