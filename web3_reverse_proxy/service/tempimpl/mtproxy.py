import threading
import time

from config.conf import BLOCKING_ACCEPT_TIMEOUT
from core.inbound.server import InboundServer
from core.sockets.clientsocket import ClientSocket
from service.tempimpl.request.requesthandlerpool import RequestHandlerPool
from concurrent.futures import ThreadPoolExecutor

from service.tempimpl.requesthandler import RequestHandler


class Web3RPCProxyHackMT:

    def __init__(self, proxy_listen_port: int, endpoint: str, endpoint_port: int, num_workers: int) -> None:
        self.inbound_srv = InboundServer(proxy_listen_port, BLOCKING_ACCEPT_TIMEOUT)
        self.endpoint = endpoint
        self.endpoint_port = endpoint_port
        self.num_workers = num_workers
        self.prev_val = 0
        self.pool = RequestHandlerPool(endpoint, endpoint_port, "pass_thru")

        print(f"Launching hack MT proxy on port {proxy_listen_port} with {num_workers} worker threads")
        print(f"Using local geth  endpoint {endpoint}:{endpoint_port}")

    def handle_client(self, handler: RequestHandler, cs: ClientSocket) -> RequestHandler:
        handler.handle_request(cs)
        return handler

    def client_handled_callback(self, future) -> None:
        handler = future.result()
        self.pool.release(handler)

    def update_stats(self):
        while True:
            time.sleep(0.2)
            if RequestHandler.NUM_REQ - self.prev_val > 20:
                print(f"\rNumber of processed requests: {RequestHandler.NUM_REQ}", end="")
                self.prev_val = RequestHandler.NUM_REQ

    def main_loop(self) -> None:
        srv_socket = self.inbound_srv.server_s

        t = threading.Thread(target=self.update_stats, daemon=True)
        t.start()

        with ThreadPoolExecutor(self.num_workers) as executor:
            while True:
                cs = None
                while cs is None:
                    cs = srv_socket.accept(BLOCKING_ACCEPT_TIMEOUT)

                executor.submit(self.handle_client, self.pool.get(), cs).add_done_callback(self.client_handled_callback)

    def run_forever(self) -> None:
        try:
            self.main_loop()
        except KeyboardInterrupt:
            print()
            print("Interrupted by user - shutting down")
            self.inbound_srv.server_s.close()
        except Exception:
            raise
