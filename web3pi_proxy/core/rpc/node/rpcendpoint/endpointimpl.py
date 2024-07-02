from __future__ import annotations

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import (
    EndpointConnectionStats,
)


class RPCEndpoint:
    def __init__(self, name, conn_descr: EndpointConnectionDescriptor) -> None:
        self.conn_descr = conn_descr
        self.name = name
        self.conn_stats = EndpointConnectionStats()

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, addr={self.get_endpoint_addr()})"

    def get_endpoint_addr(self) -> str:
        return f"{self.conn_descr.host}:{self.conn_descr.port}"

    def get_name(self) -> str:
        return self.name

    def get_connection_stats(self) -> EndpointConnectionStats:
        return self.conn_stats

    def update_stats(self, request_bytes: bytearray, response_bytes: bytearray) -> None:
        self.conn_stats.update_request_bytes(request_bytes)
        self.conn_stats.update_response_bytes(response_bytes)

    @classmethod
    def create(cls, name: str, conn_descr: EndpointConnectionDescriptor) -> RPCEndpoint:
        return RPCEndpoint(name, conn_descr)
