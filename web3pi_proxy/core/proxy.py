import queue
import select
import threading
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from mypy.nodes import node_kinds

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.inbound.server import InboundServer
from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.rpc.node.endpoint_pool.trusted_node_verifier import TrustedNodeVerifier
from web3pi_proxy.core.sockets.poller import (
    get_poller,
    Poller,
    POLLIN,
)
from web3pi_proxy.core.rpc.node.client_socket_pool import ClientSocketPool
from web3pi_proxy.core.rpc.node.endpoint_pool.pool_manager import (
    EndpointConnectionPoolManager,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import (
    BrokenConnectionError,
    EndpointConnectionHandler,
)
from web3pi_proxy.core.rpc.request.middleware.requestmiddlewaredescr import (
    RequestMiddlewareDescr,
)
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.rpc.response.optionsresponse import OptionsResponses
from web3pi_proxy.core.sockets.clientsocket import ClientSocket
from web3pi_proxy.core.utilhttp.errors import ErrorResponses
from web3pi_proxy.interfaces.servicestate import StateUpdater
from web3pi_proxy.utils.logger import get_logger


class Web3RPCProxy:
    __logger = get_logger("Web3RPCProxy")

    def __init__(
        self,
        proxy_listen_address: str,
        proxy_listen_port: int,
        num_proxy_workers: int,
        middlewares: RequestMiddlewareDescr,
        connection_pool: EndpointConnectionPoolManager,
        state_updater: StateUpdater,
        trusted_node_verifier: TrustedNodeVerifier
    ) -> None:

        self.request_reader = middlewares.instantiate()

        self.__print_pre_init_info(self.request_reader, connection_pool)

        self.inbound_srv = InboundServer(
            proxy_listen_address, proxy_listen_port, Config.BLOCKING_ACCEPT_TIMEOUT
        )
        self.connection_pool = connection_pool
        self.state_updater = state_updater

        self.__print_post_init_info(proxy_listen_address, proxy_listen_port)

        self.num_workers = num_proxy_workers

        self.trusted_node_verifier = trusted_node_verifier

    @classmethod
    def __print_pre_init_info(
        cls, rr: RequestReaderMiddleware, cp: EndpointConnectionPoolManager
    ) -> None:

        print(f"Starting {Config.PROXY_NAME}, version {Config.PROXY_VER}")
        print(f"Provided request middleware chain: {rr}")

        endpoints = cp.endpoints
        print(
            f'Connected to {len(endpoints)} endpoint{"s" if len(endpoints) > 1 else ""}:',
            end="",
        )
        for i in range(len(endpoints)):
            print(
                f'{"" if i == 0 else ","} "{endpoints[i].get_name()}" @ {endpoints[i].get_endpoint_addr()}',
                end="",
            )

        print("\nInitializing proxy...")

    def __close_client_socket(self, cs: ClientSocket) -> None:
        try:
            self.__logger.debug(f"Closing client socket {cs}")
            cs.close()
        except OSError as error:
            self.__logger.error(error)
            self.__logger.error(f"Error on closing socket {cs}")

    def __close_client_connection(
        self,
        cs: ClientSocket,
        client_poller: Poller,
        active_client_connections: ClientSocketPool,
    ):
        active_client_connections.del_cs_in_use(cs.fd)
        client_poller.unregister(cs.fd)
        self.__close_client_socket(cs)

    def __manage_client_connection(
        self,
        keep_alive: bool,
        cs: ClientSocket,
        client_poller: Poller,
        active_client_connections: ClientSocketPool,
    ) -> None:
        if keep_alive:
            active_client_connections.set_cs_pending(cs.fd)
            if getattr(select, "EPOLLONESHOT", None):
                client_poller.modify(
                    cs.socket, POLLIN | select.EPOLLONESHOT
                )  # TODO hangup? errors?
        else:
            self.__close_client_connection(cs, client_poller, active_client_connections)

    def __create_response_handler(
        self,
        endpoint_connection_handler: EndpointConnectionHandler,
        cs: ClientSocket,
        req: RPCRequest,
    ) -> Callable:
        add_cors = req.cors_origin is not None  # TODO CORS support here is very crude, needs improvement

        def response_handler(res: bytes):
            if cs.socket.fileno() < 0:
                return
            nonlocal add_cors
            if add_cors:
                add_cors = False
                res = res.replace(b"\r\n", b"\r\nAccess-Control-Allow-Origin: " + req.cors_origin + b"\r\n", 1)
            cs.send_all(res)
            endpoint_connection_handler.update_response_stats(res)  # TODO do we need bytearray here?
            self.state_updater.record_rpc_response(req, res)

        return response_handler

    def handle_client(
        self,
        cs: ClientSocket,
        client_poller: Poller,
        active_client_connections: ClientSocketPool,
    ) -> None:
        endpoint_connection_handler = None
        trusted_connection_handler = None
        try:
            req, err = self.request_reader.read_request(cs, RPCRequest())

            if req is None and err is None:
                self.__manage_client_connection(
                    False, cs, client_poller, active_client_connections
                )
                return

            if err is not None:
                cs.send_all(err.raw)  # TODO: detect whether client connection is closed
                self.__manage_client_connection(
                    err.request.keep_alive, cs, client_poller, active_client_connections
                )
                return

            if req.http_method == b"OPTIONS":  # TODO CORS are always included, is that right?
                cs.send_all(
                    OptionsResponses.options_response(req)
                )
                self.__manage_client_connection(
                    req.keep_alive, cs, client_poller, active_client_connections
                )
                return

            # if self.is_cache_available:  # TODO cache
            #     self.read_cache()

            # Main node handling
            try:
                endpoint_connection_handler = self.connection_pool.get_connection(req)
            except Exception as error:
                self.__logger.error("%s: %s", error.__class__, error)
                self.__logger.error("Failed to establish endpoint connection")
                cs.send_all(
                    ErrorResponses.connection_error(req.id)
                )  # TODO: detect wether client connection is closed
                self.__manage_client_connection(
                    req.keep_alive, cs, client_poller, active_client_connections
                )
                return

            if Config.ENABLE_TRUSTED_NODE_VERIFICATION:
                # Trusted node handling
                try:
                    trusted_connection_handler = self.connection_pool.get_trusted_node_connection()
                except Exception as error:
                    self.__logger.error("%s: %s", error.__class__, error)
                    self.__logger.error("Failed to establish trusted endpoint connection")
                    self.__logger.error("Stack trace:\n%s",
                                        traceback.format_exc())
                    trusted_connection_handler = None

            # Parallel request sending
            with ThreadPoolExecutor(max_workers=2) as executor:
                fut_main = executor.submit(endpoint_connection_handler.send, req)
                fut_trusted = (
                    executor.submit(trusted_connection_handler.send, req)
                    if Config.ENABLE_TRUSTED_NODE_VERIFICATION and trusted_connection_handler
                    else None
                )

                try:
                    main_response = fut_main.result()
                    trusted_response = fut_trusted.result() if fut_trusted else None
                except Exception as e:
                    self.__logger.error(f"Error during request handling: {e}")
                    cs.send_all(ErrorResponses.connection_error(req.id))
                    endpoint_connection_handler.update_error_stats(1)
                    endpoint_connection_handler.close()

                    if trusted_connection_handler:
                        trusted_connection_handler.close()
                    self.__manage_client_connection(
                        req.keep_alive, cs, client_poller, active_client_connections
                    )
                    return

                print(f"main_response: {main_response}")
                print(f"trusted_response: {trusted_response}")

            if trusted_response and not self.trusted_node_verifier.verify(req, main_response, trusted_response):
                endpoint_connection_handler.update_error_stats(0, 1)
                self.__logger.error("""Trusted node response does not match node response""")
                response_handler = self.__create_response_handler(
                    trusted_connection_handler, cs, req
                )
            else:
                response_handler = self.__create_response_handler(
                    endpoint_connection_handler, cs, req
                )

            try:
                endpoint_connection_handler.receive(response_handler)
            except (
                BrokenConnectionError
            ):  # TODO: Pick up new connection from pool if fresh connection failed
                self.__logger.error(
                    f"Failed to receive response with {endpoint_connection_handler}"
                )
                cs.send_all(
                    ErrorResponses.connection_error(req.id)
                )  # TODO: detect whether client connection is closed
                self.__manage_client_connection(
                    req.keep_alive, cs, client_poller, active_client_connections
                )
                endpoint_connection_handler.close()
                return

            # if self.is_cache_available and \  # TODO cache
            #         self.response_cache.is_writeable(response.request) and \
            #         self.response_cache.get(response.request.method) is None:
            #     self.response_cache.store(response.request.method, response)
            endpoint_connection_handler.update_request_stats(req)
            self.state_updater.record_rpc_request(req)
            self.__manage_client_connection(
                req.keep_alive, cs, client_poller, active_client_connections
            )
            endpoint_connection_handler.release()

        except Exception as e:
            traceback.print_exc()
            self.__logger.error(e)
            print(
                f"Error while handling the client request {e}"
            )  # TODO is this a good error handling?
            self.__close_client_connection(cs, client_poller, active_client_connections)
            if endpoint_connection_handler:
                endpoint_connection_handler.release()

    @classmethod
    def __print_post_init_info(cls, proxy_listen_address, proxy_listen_port: int) -> None:
        print(
            "Proxy initialized and listening on {}".format(
                f"{proxy_listen_address}:{proxy_listen_port}"
            )
        )

    def closing_cs(self, client_poller: Poller, queue_cs_for_close: queue.Queue):
        while True:
            cs = queue_cs_for_close.get()
            client_poller.unregister(cs.fd)
            self.__close_client_socket(cs)

    def main_loop(self) -> None:
        client_poller = get_poller()
        srv_socket = self.inbound_srv.server_s  # TODO async?
        client_poller.register(
            srv_socket.socket, POLLIN
        )  # TODO EPOLLHUP? EPOLLERR? EPOLLRDHUP?
        # TODO Implement Keep-Alive http header
        active_client_connections = ClientSocketPool()  # TODO close stale connections

        fd_lock = defaultdict(threading.Lock)

        queue_cs_for_close = queue.Queue()
        t = threading.Thread(
            target=self.closing_cs,
            args=(client_poller, queue_cs_for_close),
            daemon=True,
        )
        t.start()

        with ThreadPoolExecutor(self.num_workers) as executor:
            while True:
                pending_cs_size = active_client_connections.get_size()
                while pending_cs_size > Config.MAX_PENDING_CLIENT_SOCKETS:
                    cs = active_client_connections.pop_cs_pending_from_tail()
                    queue_cs_for_close.put(cs)
                    pending_cs_size = pending_cs_size - 1

                events = client_poller.poll(Config.BLOCKING_ACCEPT_TIMEOUT)
                for fd, ev in events:
                    if fd == srv_socket.socket.fileno():
                        cs = srv_socket.accept_awaiting_connection()  # TODO connection hang up? errors?
                        active_client_connections.add_cs_pending(cs)
                        try:
                            client_poller.register(
                                cs.socket, POLLIN | select.EPOLLONESHOT
                            )  # TODO hangup? errors?
                        except AttributeError:
                            client_poller.register(cs.socket, POLLIN)
                    else:
                        with fd_lock[fd]:
                            try:
                                if active_client_connections.is_in_use(fd):
                                    break
                            except KeyError:
                                break
                            cs = active_client_connections.get_cs_and_set_in_use(
                                fd
                            )
                        # TODO connection hang up?
                        executor.submit(
                            self.handle_client,
                            cs,
                            client_poller,
                            active_client_connections,
                        )

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
