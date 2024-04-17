from web3_reverse_proxy.config.conf import Config

from web3_reverse_proxy.core.inbound.server import InboundServer
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware

from web3_reverse_proxy.core.stats.proxystats import RPCProxyStats

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.interfaces.rpcresponse import RPCResponseHandler

from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import RequestMiddlewareDescr
from web3_reverse_proxy.core.rpc.rpcrequestmanager import RPCProxyRequestManager
from web3_reverse_proxy.core.rpc.cache.responsecacheservice import ResponseCacheService


class Web3RPCProxy:

    def __init__(
            self,
            proxy_listen_port: int,
            middlewares: RequestMiddlewareDescr,
            endpoints_handler: EndpointsHandler,
            response_handler: RPCResponseHandler,
            cache_service: ResponseCacheService
        ) -> None:

        request_reader = middlewares.instantiate()

        self.__print_pre_init_info(request_reader, endpoints_handler)

        self.inbound_srv = InboundServer(proxy_listen_port, Config.BLOCKING_ACCEPT_TIMEOUT)
        self.request_manager = RPCProxyRequestManager(
            request_reader,
            endpoints_handler,
            response_handler,
            cache_service,
        )

        self.__print_post_init_info(proxy_listen_port)

        self.stats = RPCProxyStats()

    @classmethod
    def __print_pre_init_info(cls, rr: RequestReaderMiddleware, eh: EndpointsHandler) -> None:

        print(f'Starting {Config.PROXY_NAME}, version {Config.PROXY_VER}')
        print(f'Provided request middleware chain: {rr}')

        endpoints = list(eh.get_endpoints())
        print(f'Connected to {len(endpoints)} endpoint{"s" if len(endpoints) > 1 else ""}:', end="")
        for i in range(len(endpoints)):
            print(f'{"" if i == 0 else ","} "{endpoints[i].get_name()}" @ {endpoints[i].get_endpoint_addr()}', end="")

        print('\nInitializing proxy...')

    @classmethod
    def __print_post_init_info(cls, proxy_listen_port: int) -> None:
        print("Proxy initialized and listening on {}".format(f"{Config.PROXY_LISTEN_ADDRESS}:{proxy_listen_port}"))

    def main_loop(self) -> None:
        while True:
            # Handle incoming connections
            incoming_connections_num = self.inbound_srv.accept_incoming_connections()
            ready_read_connections = self.inbound_srv.remove_ready_read_connections()

            # Handle incoming requests
            self.request_manager.handle_requests(ready_read_connections)

            # Handle request sockets used in this iteration
            processed_requests_num = self.request_manager.get_num_processed_requests()

            # Read back state after processing step
            sockets_to_close = self.request_manager.get_sockets_to_close()
            processed_sockets = self.request_manager.get_processed_sockets()

            # Update inbound server state
            closed_connections_num = self.inbound_srv.close_connections(sockets_to_close)
            self.inbound_srv.add_active_connections(processed_sockets)

            # Basic bookkeeping
            self.stats.update(incoming_connections_num, processed_requests_num, closed_connections_num)
            if self.stats.is_ready_to_update_display():
                self.stats.display_rudimentary_stats()

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
