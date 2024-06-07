from unittest import TestCase
from unittest.mock import Mock, patch

from web3_reverse_proxy.core.proxy import Web3RPCProxy

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import RequestMiddlewareDescr
from web3_reverse_proxy.core.rpc.node.client_socket_pool import ClientSocketPool
from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler


class Web3RPCProxyTestCase(TestCase):
    def setUp(self):
        self.middlewares = Mock()
        self.endpoints_handler = Mock(),
        self.connection_pool = Mock()

    def create_proxy(self, proxy_listen_port=8545, num_proxy_workers=150):
        with (
            patch(
                "web3_reverse_proxy.core.proxy.Config",
                BLOCKING_ACCEPT_TIMEOUT = 5,
                PROXY_NAME="Web3 RPC Reverse Proxy - Test",
                PROXY_VER="0.0.1",
                PROXY_LISTEN_ADDRESS="0.0.0.0",
                MAX_PENDING_CLIENT_SOCKETS=10_000,
            ),
            patch("web3_reverse_proxy.core.proxy.InboundServer"),
            patch("web3_reverse_proxy.core.proxy.RPCProxyStats"),
        ):
            return Web3RPCProxy(proxy_listen_port, num_proxy_workers, middlewares, endpoints_handler, connection_pool)


class HandleClientTests(Web3RPCProxyTestCase):
    def setUp(self):
        pass

    def test_success(self):
        pass

    def test_error_on_request_read(self):
        pass

    def test_error_on_request_read_with_keep_alive(self):
        pass

    def test_error_on_request_send(self):
        pass

    def test_error_on_endpoint_reconnect(self):
        pass

    def test_error_on_endpoint_reconnect_with_keep_alive(self):
        pass

    def test_unexpected_error(self):
        pass
    # def __init__(
    #         self,
    #         proxy_listen_port: int,
    #         num_proxy_workers: int,
    #         middlewares: RequestMiddlewareDescr,
    #         endpoints_handler: EndpointsHandler,
    #         connection_pool: ConnectionPool,
    #     ) -> None:

    #     self.request_reader = middlewares.instantiate()

    #     self.__print_pre_init_info(self.request_reader, endpoints_handler)

    #     self.inbound_srv = InboundServer(proxy_listen_port, Config.BLOCKING_ACCEPT_TIMEOUT)
    #     self.connection_pool = connection_pool

    #     self.__print_post_init_info(proxy_listen_port)

    #     self.stats = RPCProxyStats()

    #     self.num_workers = num_proxy_workers

    # def handle_client(
    #         self,
    #         endpoint_connection_handler: ConnectionHandler,
    #         cs: ClientSocket,
    #         client_poller: select.epoll,
    #         active_client_connections: ClientSocketPool
    #     ) -> None: