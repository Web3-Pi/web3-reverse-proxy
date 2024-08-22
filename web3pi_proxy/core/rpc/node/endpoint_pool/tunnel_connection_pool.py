import socket

from web3pi_proxy.config import Config
from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import EndpointConnectionPool
from web3pi_proxy.core.rpc.node.endpoint_pool.tunnel_connection_pool_intf import TunnelConnectionPoolIntf
from web3pi_proxy.core.rpc.node.endpoint_pool.tunnel_service import TunnelService
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.tunnelendpointconnection import TunnelEndpointConnection
from web3pi_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint

from web3pi_proxy.utils.logger import get_logger


class TunnelConnectionPool(EndpointConnectionPool, TunnelConnectionPoolIntf):

    def __init__(
        self,
        endpoint: RPCEndpoint,
    ):
        super().__init__(endpoint)
        self.__logger = get_logger(f"TunnelConnectionPool.{id(self)}")

        self.tunnel_api_key = endpoint.conn_descr.extras["tunnel_service_auth_key"]
        self.tunnel_proxy_establish_port: int = endpoint.conn_descr.extras["tunnel_proxy_establish_port"]

        tunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tunnel_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tunnel_socket.bind((Config.PROXY_LISTEN_ADDRESS, self.tunnel_proxy_establish_port))
        tunnel_socket.listen(Config.LISTEN_BACKLOG_PARAM)
        self.tunnel_socket = tunnel_socket

        self.tunnel_service_socket = None

        self.status = self.PoolStatus.DISABLED.value

        TunnelService.register(self.tunnel_api_key, self)

    def new_connection(self) -> EndpointConnection:

        def connection_factory() -> socket:  # TODO is it worth to move it to object level and reuse?
            self.__logger.debug("Creating socket")
            self.tunnel_service_socket.sendall(b"NEWCONN")
            new_conn_sock, new_conn_addr = self.tunnel_socket.accept()
            self.__logger.debug("Finished connecting socket")
            return new_conn_sock

        return TunnelEndpointConnection(self.endpoint, connection_factory)

    def new_tunnel_service_socket(self, tunnel_service_socket: socket):
        with self._EndpointConnectionPool__lock:
            self.tunnel_service_socket = tunnel_service_socket
            self.status = self.PoolStatus.ACTIVE.value

    def close(self) -> None:
        super().close()
        self.tunnel_socket.close()
        self.tunnel_socket = None
        if self.tunnel_service_socket:
            self.tunnel_service_socket.close()
            self.tunnel_service_socket = None
        TunnelService.unregister(self.tunnel_api_key, self)
