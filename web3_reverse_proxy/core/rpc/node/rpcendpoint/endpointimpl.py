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
        self.active_connections = []

    def _get_connection_response_handler(
            self,
            req: RPCRequest,
            conn: EndpointConnection,
            outer_handler: Callable
        ) -> Callable:
        def connection_response_handler(res: RPCResponse):
            self.state_updater.record_processed_rpc_call(req, res)
            self.conn_stats.append(conn.stats)
            return outer_handler(res)
        return connection_response_handler

    def get_endpoint_addr(self) -> str:
        return f"{self.conn_descr.host}:{self.conn_descr.port}"

    def get_name(self) -> str:
        return self.name

    def get_connection_stats(self) -> EndpointConnectionStats:
        return self.conn_stats

    def handle_request_response_roundtrip(self, req: RPCRequest, callback: Callable) -> None:
        self._logger.debug(f"Creating connection from description: {self.conn_descr}")
        conn = EndpointConnection.create(self.conn_descr)
        self.active_connections.append(conn)
        try:
            self._logger.debug(f"Send/receive roundtrip for connection {conn} with request {req}")
            conn.send_recv_roundtrip(req, self._get_connection_response_handler(req, conn, callback))
        except IOError:
            self._logger.debug(f"Reconnect due to IOError for connection {conn}")
            conn.reconnect()
            self._logger.debug(f"Send/receive roundtrip for connection {conn} with request {req}")
            conn.send_recv_roundtrip(req, self._get_connection_response_handler(req, conn, callback))
        except Exception:
            raise

        self._logger.debug(f"Closing connection: {conn}")
        conn.socket.close()
        self.active_connections.remove(conn)

    def close(self):
        for conn in self.active_connections:
            self._logger.debug(f"Closing active connection: {conn}")
            conn.socket.close()

    @classmethod
    def create(cls, name: str, conn_descr: EndpointConnectionDescriptor, state_updater: StateUpdater) -> RPCEndpoint:
        return RPCEndpoint(name, conn_descr, state_updater)
