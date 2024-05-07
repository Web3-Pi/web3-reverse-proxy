from __future__ import annotations

from typing import List, Tuple
from threading import Lock

from web3_reverse_proxy.core.interfaces.rpcnode import LoadBalancer
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.loadbalancers.simpleloadbalancers import RandomLoadBalancer
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import EndpointConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool

from web3_reverse_proxy.interfaces.servicestate import StateUpdater
from web3_reverse_proxy.utils.logger import get_logger


class EndpointConnectionPool(ConnectionPool):
    _logger = get_logger("EndpointConnectionPool")
    MAX_CONNECTIONS = 10

    def __init__(
            self,
            descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
            state_updater: StateUpdater,
            load_balancer: LoadBalancer = RandomLoadBalancer,  # For convenience during architecture change
        ):
        self.endpoints = []
        self.load_balancer = load_balancer
        self.connections = []
        self.lock = Lock()

        for index in range(len(descriptors)):
            name, conn_descr = descriptors[index]
            assert conn_descr is not None
            self._logger.debug(f"Creating endpoint {name} with connection {conn_descr}")
            self.endpoints.append(RPCEndpoint.create(name, conn_descr, state_updater))

    def _cleanup(self) -> None:
        while len(self.connections) > self.MAX_CONNECTIONS:
            connection = self.connections.pop()
            try:
                connection.close()
            except OSError as error:
                self._logger.error(error)

    def get(self) -> ConnectionHandler:
        self._logger.debug("Selecting endpoint connection from pool")
        if len(self.connections) == 0:
            self._logger.debug("No existing connections available, establishing new connection")
            # TODO: Reconsider load balancers after new architecture is settled
            endpoint_index = self.load_balancer.get_queue_for_request(self.endpoints, RPCRequest())
            connection = self.endpoints[endpoint_index].create_connection()
        else:
            self.lock.acquire()
            connection = self.connections.pop()
            self.lock.release()
        self._logger.debug(f"Return connection {connection}")
        return EndpointConnectionHandler(connection, self)

    def put(self, connection: EndpointConnection) -> None:
        self._logger.debug(f"Putting connection {connection} to pool")
        self.lock.acquire()
        self.connections.append(connection)
        self._cleanup()
        self.lock.release()

    # Intended for cleaning after shutdown
    def close(self) -> None:
        self.lock.acquire()
        for connection in self.connections:
            try:
                connection.close()
            except OSError as error:
                self._logger.error(error)
        self.lock.release()
