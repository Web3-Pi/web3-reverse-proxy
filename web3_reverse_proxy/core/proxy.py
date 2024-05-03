from web3_reverse_proxy.config.conf import Config

from web3_reverse_proxy.core.inbound.server import InboundServer
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware

from web3_reverse_proxy.core.stats.proxystats import RPCProxyStats

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.interfaces.rpcresponse import RPCResponseHandler

from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket

from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import RequestMiddlewareDescr
from web3_reverse_proxy.core.rpc.rpcrequestmanager import RPCProxyRequestManager
from web3_reverse_proxy.core.rpc.cache.responsecacheservice import ResponseCacheService
from web3_reverse_proxy.core.rpc.node.endpoint_connection_pool import EndpointConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest

from concurrent.futures import ThreadPoolExecutor


class Web3RPCProxy:

    def __init__(
            self,
            proxy_listen_port: int,
            middlewares: RequestMiddlewareDescr,
            endpoints_handler: EndpointsHandler,
            connection_pool: EndpointConnectionPool,
            response_handler: RPCResponseHandler,
            cache_service: ResponseCacheService
        ) -> None:

        self.request_reader = middlewares.instantiate()

        self.__print_pre_init_info(self.request_reader, endpoints_handler)

        self.inbound_srv = InboundServer(proxy_listen_port, Config.BLOCKING_ACCEPT_TIMEOUT)
        self.request_manager = RPCProxyRequestManager(
            self.request_reader,
            endpoints_handler,
            response_handler,
            cache_service,
        )
        self.connection_pool = connection_pool

        self.__print_post_init_info(proxy_listen_port)

        self.stats = RPCProxyStats()

        self.num_workers = 100

    @classmethod
    def __print_pre_init_info(cls, rr: RequestReaderMiddleware, eh: EndpointsHandler) -> None:

        print(f'Starting {Config.PROXY_NAME}, version {Config.PROXY_VER}')
        print(f'Provided request middleware chain: {rr}')

        endpoints = list(eh.get_endpoints())
        print(f'Connected to {len(endpoints)} endpoint{"s" if len(endpoints) > 1 else ""}:', end="")
        for i in range(len(endpoints)):
            print(f'{"" if i == 0 else ","} "{endpoints[i].get_name()}" @ {endpoints[i].get_endpoint_addr()}', end="")

        print('\nInitializing proxy...')

    def handle_client(self, endpoint_connection_handler: ConnectionHandler, cs: ClientSocket) -> None:
        req, err = self.request_reader.read_request(cs, RPCRequest())

        if err is not None:
            pass  # TODO errors
        # if self.is_cache_available:  # TODO cache
        #     self.read_cache()
        endpoint_req_bytes = endpoint_connection_handler.get_sender().send_request(req)  # TODO reconnect?
        # self.stats.update(endpoint_req_bytes, res_bytes)  # TODO stats

        def response_handler(res):
            cs.send_all(res)  # TODO errors
            # self.stats.update(endpoint_req_bytes, res_bytes)  # TODO stats

        endpoint_connection_handler.get_receiver().recv_response(response_handler)  # TODO errors
        # if self.is_cache_available and \  # TODO cache
        #         self.response_cache.is_writeable(response.request) and \
        #         self.response_cache.get(response.request.method) is None:
        #     self.response_cache.store(response.request.method, response)

        cs.close()  # TODO keep alive management

        endpoint_connection_handler.release()

        #     # Basic bookkeeping  # TODO stats
        #     self.stats.update(incoming_connections_num, processed_requests_num, closed_connections_num)
        #     if self.stats.is_ready_to_update_display():
        #         self.stats.display_rudimentary_stats()

    @classmethod
    def __print_post_init_info(cls, proxy_listen_port: int) -> None:
        print("Proxy initialized and listening on {}".format(f"{Config.PROXY_LISTEN_ADDRESS}:{proxy_listen_port}"))

    def main_loop(self) -> None:
        srv_socket = self.inbound_srv.server_s

        with ThreadPoolExecutor(self.num_workers) as executor:
            while True:
                cs = None
                while cs is None:
                    cs = srv_socket.accept(Config.BLOCKING_ACCEPT_TIMEOUT)

                executor.submit(self.handle_client, self.connection_pool.get(), cs)

        # TODO when close the connection pool?

    def cleanup(self) -> None:
        print()
        print("Proxy interrupted - shutting down endpoint(s)")
        self.request_manager.shut_down()

        print("Proxy interrupted - shutting down proxy server")
        self.inbound_srv.shutdown()

    def run_forever(self) -> None:
        try:
            self.main_loop()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception:
            raise
