from __future__ import annotations

from abc import ABCMeta, abstractmethod

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import (
    ConnectionHandler,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import (
    EndpointConnection,
)


class ConnectionPool(metaclass=ABCMeta):
    @abstractmethod
    def get(self) -> ConnectionHandler:
        pass

    @abstractmethod
    def put(self, connection: EndpointConnection) -> None:
        pass

    # Intended for cleaning after shutdown
    @abstractmethod
    def close(self) -> None:
        pass
