from __future__ import annotations

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import EndpointConnectionStats
from web3_reverse_proxy.interfaces.servicestate import StateUpdater

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection


class RPCEndpoint:

    def __init__(self, name, connection: EndpointConnection, state_updater: StateUpdater) -> None:
        self.conn = connection
        self.state_updater = state_updater
        self.name = name

    def get_endpoint_addr(self) -> str:
        return f"{self.conn.host}:{self.conn.port}"

    def get_name(self) -> str:
        return self.name

    def get_connection_stats(self) -> EndpointConnectionStats:
        return self.conn.stats

    def handle_request_response_roundtrip(self, req: RPCRequest) -> RPCResponse:
        try:
            res = self.conn.send_recv_roundtrip(req)
            print(f"Received response: {res}")
        except IOError:
            print(f"IOError, trying to reconnect")
            self.conn.reconnect()
            res = self.conn.send_recv_roundtrip(req)
        except Exception:
            raise

        self.state_updater.record_processed_rpc_call(req, res)

        return res

    def close(self):
        self.conn.socket.close()

    @classmethod
    def create(cls, name: str, conn_descr: EndpointConnectionDescriptor, state_updater: StateUpdater) -> RPCEndpoint:
        return RPCEndpoint(name, EndpointConnection.create(conn_descr), state_updater)
