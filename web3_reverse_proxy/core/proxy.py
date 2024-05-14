import select
import threading
import queue

from web3_reverse_proxy.config.conf import Config

from web3_reverse_proxy.core.inbound.server import InboundServer
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.stats.proxystats import RPCProxyStats
from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import RequestMiddlewareDescr
from web3_reverse_proxy.core.rpc.node.client_socket_pool import ClientSocketPool
from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses

from web3_reverse_proxy.utils.logger import get_logger

from concurrent.futures import ThreadPoolExecutor


class Web3RPCProxy:
    _logger = get_logger('Web3RPCProxy')

    def __init__(
            self,
            proxy_listen_port: int,
            num_proxy_workers: int,
            middlewares: RequestMiddlewareDescr,
            endpoints_handler: EndpointsHandler,
            connection_pool: ConnectionPool,
        ) -> None:

        self.request_reader = middlewares.instantiate()

        self.__print_pre_init_info(self.request_reader, endpoints_handler)

        self.inbound_srv = InboundServer(proxy_listen_port, Config.BLOCKING_ACCEPT_TIMEOUT)
        self.connection_pool = connection_pool

        self.__print_post_init_info(proxy_listen_port)

        self.stats = RPCProxyStats()

        self.num_workers = num_proxy_workers

    @classmethod
    def __print_pre_init_info(cls, rr: RequestReaderMiddleware, eh: EndpointsHandler) -> None:

        print(f'Starting {Config.PROXY_NAME}, version {Config.PROXY_VER}')
        print(f'Provided request middleware chain: {rr}')

        endpoints = list(eh.get_endpoints())
        print(f'Connected to {len(endpoints)} endpoint{"s" if len(endpoints) > 1 else ""}:', end="")
        for i in range(len(endpoints)):
            print(f'{"" if i == 0 else ","} "{endpoints[i].get_name()}" @ {endpoints[i].get_endpoint_addr()}', end="")

        print('\nInitializing proxy...')

    def __close_client_socket(self, cs: ClientSocket) -> None:
        try:
            self._logger.debug(f"Closing client socket {cs}")
            cs.close()
        except OSError as error:
            self._logger.error(error)
            self._logger.error(f"Error on closing socket {cs}")

    def __manage_client_connection(
            self,
            req: RPCRequest,
            cs: ClientSocket,
            client_poller: select.epoll,
            active_client_connections: ClientSocketPool,
        ) -> None:
            if req.keep_alive:
                active_client_connections.set_cs_pending(cs.socket.fileno())
                client_poller.modify(cs.socket, select.EPOLLIN | select.EPOLLONESHOT)  # TODO hangup? errors?
                # self.__close_client_socket(cs)  # TODO if this is commented out, rpc-tests are 30% faster, why?
            else:
                active_client_connections.del_cs_in_use(cs.socket.fileno())
                client_poller.unregister(cs.socket.fileno())
                self.__close_client_socket(cs)

    def __send_back_to_client(self, cs: ClientSocket, data: bytearray) -> None:
        try:
            cs.send_all(data)
        except:
            self._logger.error(f"Failed to send response on socket {cs}")


    def handle_client(
            self,
            endpoint_connection_handler: ConnectionHandler,
            cs: ClientSocket,
            client_poller: select.epoll,
            active_client_connections: ClientSocketPool
        ) -> None:
        try:
            # TODO detect closed by a client cs connection and close it by our side?
            req, err = self.request_reader.read_request(cs, RPCRequest())  # TODO close connection if fatal error i.e. non http request

            if err is not None:
                self.__send_back_to_client(cs, err.raw)

                if not err.request.keep_alive:
                    active_client_connections.del_cs_in_use(cs.socket.fileno())
                    client_poller.unregister(cs.socket.fileno())
                    self.__close_client_socket(cs)

                endpoint_connection_handler.release()
                return

            # if self.is_cache_available:  # TODO cache
            #     self.read_cache()
            try:
                endpoint_req_bytes = endpoint_connection_handler.get_sender().send_request(req)
            except:
                self._logger.error(f"Failed to send request {req} over connection {endpoint_connection_handler}")
                self._logger.debug(f"Reconnecting {endpoint_connection_handler}")
                endpoint_connection_handler.reconnect()
                try:
                    endpoint_req_bytes = endpoint_connection_handler.get_sender().send_request(req)
                except:
                    self._logger.error(f"Cannot reach endpoint {endpoint_connection_handler.get_ip_address()}")
                    self.__send_back_to_client(cs, ErrorResponses.http_internal_server_error())
                    self.__manage_client_connection(req, cs, client_poller, active_client_connections)
                    endpoint_connection_handler.close()
                    return

            # self.stats.update(endpoint_req_bytes, res_bytes)  # TODO stats

            def response_handler(res):
                self.__send_back_to_client(cs, res)
                # self.stats.update(endpoint_req_bytes, res_bytes)  # TODO stats

            endpoint_connection_handler.get_receiver().recv_response(response_handler)  # TODO errors
            # if self.is_cache_available and \  # TODO cache
            #         self.response_cache.is_writeable(response.request) and \
            #         self.response_cache.get(response.request.method) is None:
            #     self.response_cache.store(response.request.method, response)

            self.__manage_client_connection(req, cs, client_poller, active_client_connections)
            endpoint_connection_handler.release()

            #     # Basic bookkeeping  # TODO stats
            #     self.stats.update(incoming_connections_num, processed_requests_num, closed_connections_num)
            #     if self.stats.is_ready_to_update_display():
            #         self.stats.display_rudimentary_stats()
        except Exception as e:
            self._logger.error(e)
            print(f"Error while handling the client request {e}")  # TODO is this a good error handling?
            endpoint_connection_handler.release()
            active_client_connections.del_cs_in_use(cs.socket.fileno())
            client_poller.unregister(cs.socket.fileno())
            self.__close_client_socket(cs)

    @classmethod
    def __print_post_init_info(cls, proxy_listen_port: int) -> None:
        print("Proxy initialized and listening on {}".format(f"{Config.PROXY_LISTEN_ADDRESS}:{proxy_listen_port}"))

    def closing_cs(self, client_poller: select.epoll, queue_cs_for_close: queue.Queue):
        while True:
            cs = queue_cs_for_close.get()
            client_poller.unregister(cs.socket.fileno())
            self.__close_client_socket(cs)

    def main_loop(self) -> None:
        client_poller = select.epoll()
        srv_socket = self.inbound_srv.server_s  # TODO async?
        client_poller.register(srv_socket.socket, select.EPOLLIN)  # TODO EPOLLHUP? EPOLLERR? EPOLLRDHUP?
        # TODO Implement Keep-Alive http header
        active_client_connections = ClientSocketPool()  # TODO close stale connections

        queue_cs_for_close = queue.Queue()
        t = threading.Thread(target=self.closing_cs, args=(client_poller, queue_cs_for_close), daemon=True)
        t.start()

        with ThreadPoolExecutor(self.num_workers) as executor:
            while True:
                pending_cs_size = active_client_connections.get_size()
                while pending_cs_size > Config.MAX_PENDING_CLIENT_SOCKETS:
                    cs = active_client_connections.pop_cs_pending_from_tail()
                    queue_cs_for_close.put(cs)
                    pending_cs_size = pending_cs_size - 1

                events = client_poller.poll(Config.BLOCKING_ACCEPT_TIMEOUT)
                for fd, flag in events:
                    if fd == srv_socket.socket.fileno():
                        cs = srv_socket.accept(0)  # TODO connection hang up? errors?
                        active_client_connections.add_cs_pending(cs)
                        client_poller.register(cs.socket, select.EPOLLIN | select.EPOLLONESHOT)  # TODO hangup? errors?
                    else:
                        cs = active_client_connections.get_cs_and_set_in_use(fd)  # TODO what if does not exist
                        # TODO connection hang up?
                        executor.submit(self.handle_client, self.connection_pool.get(), cs, client_poller,
                                        active_client_connections)

        # TODO when close the connection pool?
        # TODO clean up active client connections, where?
        # TODO clients poller close, where?

    def cleanup(self) -> None:
        print()

        print("Proxy interrupted - closing node connections")
        self.connection_pool.close()

        print("Proxy interrupted - shutting down proxy server")
        self.inbound_srv.shutdown()

    def run_forever(self) -> None:
        try:
            self.main_loop()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception:
            raise
