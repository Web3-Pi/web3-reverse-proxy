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

from web3_reverse_proxy.utils.logger import get_logger


class EndpointConnectionPool(ConnectionPool):
    __logger = get_logger("EndpointConnectionPool")
    MAX_CONNECTIONS = Config.NUM_PROXY_WORKERS

    def __init__(
            self,
            descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
            load_balancer: LoadBalancer = RandomLoadBalancer,  # For convenience during architecture change
        ):
        self.endpoints = []
        self.load_balancer = load_balancer
        self.connections = SimpleQueue()
        self.__lock = Lock()

        for index in range(len(descriptors)):
            name, conn_descr = descriptors[index]
            assert conn_descr is not None
            self.__logger.debug(f"Creating endpoint {name} with connection {conn_descr}")
            self.endpoints.append(RPCEndpoint.create(name, conn_descr))

    def _cleanup(self) -> None:
        excessive_connections = self.connections.qsize() - self.MAX_CONNECTIONS
        if excessive_connections > 0:
            self.__logger.debug(f"Detected {excessive_connections} excessive connections")
            for _ in range(excessive_connections):
                connection = self.connections.get_nowait()
                self.__logger.debug(f"Removed connection {connection}")
                try:
                    connection.close()  # TODO: Move out of lock for better performance
                except OSError:
                    self.__logger.error(f"Failure on closing connection {connection}")

    def get(self) -> EndpointConnectionHandler:
        self.__logger.debug("Selecting endpoint connection from pool")

        self.__lock.acquire()
        if self.connections.empty():
            try:
                self.__logger.debug("No existing connections available, establishing new connection")
                # TODO: Reconsider load balancers after new architecture is settled
                # TODO: Could be released sooner, if endpoints remain constant
                endpoint_index = self.load_balancer.get_queue_for_request(self.endpoints, RPCRequest())
            finally:
                self.__lock.release()

            connection = EndpointConnection(self.endpoints[endpoint_index])
            is_fresh_connection = True
        else:
            try:
                connection = self.connections.get_nowait()
                is_fresh_connection = False
            finally:
                self.__lock.release()

        self.__logger.debug(f"Return connection {connection}")
        return EndpointConnectionHandler(connection, self, is_fresh_connection)

    def put(self, connection: EndpointConnection) -> None:
        self.__logger.debug(f"Putting connection {connection} to pool")
        with self.__lock:
            self.connections.put(connection)
            self._cleanup()

    def get_endpoints(self):
        return self.endpoints

    # Intended for cleaning after shutdown
    def close(self) -> None:
        with self.__lock:
            while not self.connections.empty():
                connection = self.connections.get_nowait()
                try:
                    connection.close()
                except OSError:
                    self.__logger.error(f"Failure on closing connection {connection}")
