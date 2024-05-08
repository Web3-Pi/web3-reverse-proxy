from abc import ABC

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection


class ConnectionPool(ABC):
    def get(self) -> ConnectionHandler:
        pass

    def put(self, connection: EndpointConnection) -> None:
        pass

    # Intended for cleaning after shutdown
    def close(self) -> None:
        pass
