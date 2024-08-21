import socket
import select
from threading import Lock, Thread

from web3pi_proxy.config import Config
from web3pi_proxy.core.rpc.node.endpoint_pool.tunnel_connection_pool import TunnelConnectionPool
from web3pi_proxy.utils.logger import get_logger


class TunnelServiceImpl:
    def __init__(self):
        self.__registry = dict()
        self.__lock = Lock()
        self.__initialized = False
        self.__logger = get_logger(f"TunnelServiceImpl")

    def register(self, api_key: str, tunnel_connection_pool: TunnelConnectionPool):
        with self.__lock:
            if not self.__initialized:
                self.__initialize__()
                self.__initialized = True
            self.__registry[api_key] = tunnel_connection_pool

    def unregister(self, api_key: str, tunnel_connection_pool: TunnelConnectionPool):
        with self.__lock:
            if self.__registry.get(api_key) == tunnel_connection_pool:
                del self.__registry[api_key]

    def __initialize__(self):
        tunnel_srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tunnel_srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tunnel_srv_socket.bind((Config.PROXY_LISTEN_ADDRESS, Config.TUNNEL_ESTABLISH_PORT))
        tunnel_srv_socket.listen(Config.LISTEN_BACKLOG_PARAM)
        self.tunnel_srv_socket = tunnel_srv_socket
        self.tunnel_thread = Thread(
            target=self.__tunnel_service_run,
            daemon=True,
        )
        self.tunnel_thread.start()

    def __tunnel_service_run(self):
        while True:
            ready_read, _, _ = select.select([self.tunnel_srv_socket], [], [], Config.BLOCKING_ACCEPT_TIMEOUT)

            if len(ready_read) == 0:
                continue
            tunnel_sock, cli_addr = self.tunnel_srv_socket.accept()
            self.__logger.debug(
                f"New tunnel request from {cli_addr}"
            )

            cli_api_key = tunnel_sock.recv(2048).decode("utf-8")  # TODO the attack: a tunnel client does not send api key
            if not cli_api_key:
                tunnel_sock.close()
                continue

            with self.__lock:
                pool: TunnelConnectionPool = self.__registry.get(cli_api_key)
                if not pool:
                    tunnel_sock.close()  # TODO any response before close?
                    continue
                tunnel_sock.sendall(f'ACPT|{Config.PROXY_LISTEN_ADDRESS}:{pool.tunnel_proxy_establish_port}'.encode("utf-8"))
                pool.new_tunnel_service_socket(tunnel_sock)


TunnelService = TunnelServiceImpl()
