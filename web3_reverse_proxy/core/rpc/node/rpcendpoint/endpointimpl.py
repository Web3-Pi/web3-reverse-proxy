from __future__ import annotations

from typing import Callable

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import EndpointConnectionStats
from web3_reverse_proxy.interfaces.servicestate import StateUpdater

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection

from web3_reverse_proxy.utils.logger import get_logger


class RPCEndpoint:
    _logger = get_logger("RPCEndpoint")


    def __init__(self, name, conn_descr: EndpointConnectionDescriptor, state_updater: StateUpdater) -> None:
        self.conn_descr = conn_descr
        self.state_updater = state_updater
        self.name = name
        self.conn_stats = EndpointConnectionStats()

    def get_endpoint_addr(self) -> str:
        return f"{self.conn_descr.host}:{self.conn_descr.port}"

    def get_name(self) -> str:
        return self.name

    def get_connection_stats(self) -> EndpointConnectionStats:
        return self.conn_stats

    def create_connection(self) -> EndpointConnection:
        return EndpointConnection.create(self.conn_descr)

    @classmethod
    def create(cls, name: str, conn_descr: EndpointConnectionDescriptor, state_updater: StateUpdater) -> RPCEndpoint:
        return RPCEndpoint(name, conn_descr, state_updater)
