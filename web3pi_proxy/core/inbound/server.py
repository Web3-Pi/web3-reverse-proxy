import select
from typing import Iterable, List, Set

from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.sockets.clientsocket import ClientSocket
from web3pi_proxy.core.sockets.serversocket import ServerSocket
from web3pi_proxy.core.utilhttp.errors import ErrorResponses


class InboundServer:

    def __init__(
        self,
        listen_port: int,
        blocking_accept_timeout: int,
        max_concurrent_conn: int = Config.MAX_CONCURRENT_CONNECTIONS,
        qos_frequency: float = Config.QOS_BASE_FREQUENCY,
    ) -> None:

        self.accepted_connections = set()
        self.active_connections = set()
        self.max_concurrent_connections = max_concurrent_conn
        self.blocking_accept_timeout = blocking_accept_timeout
        self.qos_timeout = 1.0 / qos_frequency

        self.no_saturated_iterations = 0

        self.server_s = ServerSocket.create(listen_port)

    @classmethod
    def _receive_dev_null(cls, rejected: Iterable[ClientSocket]) -> None:
        # FIXME: request should (probably) be read in a more controlled manner even in this case
        for cs in rejected:
            cs.recv_discard_data()

    @classmethod
    def _close_with_error_responses(
        cls, connections: Iterable[ClientSocket], error_response: bytes
    ) -> None:
        for cs in connections:
            try:
                if cs.is_ready_write():
                    cs.send_all(error_response)
            except IOError:
                pass
            except Exception:
                raise

            cs.close()

    def handle_additional_connections(
        self, incoming: set, accept_timeout: float
    ) -> [Set, List]:
        cur_conn_num = len(self.active_connections) + len(incoming)
        rejected = []

        # Peek at new connections in case of ongoing RPC proxying to avoid starving new clients (in case of ongoing
        # rpc processing, wait a quant of time to avoid wasting CPU time on empty loop iterations)
        if cur_conn_num < self.max_concurrent_connections:
            next_client_s = self.server_s.accept(accept_timeout)
            while next_client_s is not None:
                incoming.add(next_client_s)

                cur_conn_num += 1
                if cur_conn_num == self.max_concurrent_connections:
                    break

                next_client_s = self.server_s.accept(0.0)
        elif (
            self.no_saturated_iterations > Config.MAX_SATURATED_ITERATIONS_LISTEN_PARAM
        ):
            # In this case - reject all pending connections
            next_client_s = self.server_s.accept(0.0)
            while next_client_s is not None:
                rejected.append(next_client_s)
                next_client_s = self.server_s.accept(0.0)

        return incoming, rejected

    def accept_incoming_connections(self) -> int:
        incoming = set()

        # If there are active connections available, there should be no delay in processing them (hence a 0.0 timeout)
        additional_connections_accept_timeout = (
            self.qos_timeout if len(self.active_connections) == 0 else 0.0
        )

        # If there are no accepted connections, wait for the new one (timeout allows for keyboard interrupt handling)
        if len(self.accepted_connections) == 0:
            additional_connections_accept_timeout = 0.0
            next_client_s = None

            while next_client_s is None:
                next_client_s = self.server_s.accept(self.blocking_accept_timeout)

            incoming.add(next_client_s)

        incoming, rejected = self.handle_additional_connections(
            incoming, additional_connections_accept_timeout
        )

        if len(incoming) > 0:
            self.active_connections |= incoming
            self.accepted_connections |= incoming

        if len(rejected) > 0:
            self._receive_dev_null(rejected)
            self._close_with_error_responses(
                rejected, ErrorResponses.service_unavailable()
            )

        return len(incoming)

    def remove_ready_read_connections(self) -> List[ClientSocket]:
        if len(self.active_connections) == 0:
            return []

        res = {}
        for cs in self.active_connections:
            res[cs.socket] = cs

        s_read, _, _ = select.select(res.keys(), [], [], self.qos_timeout)

        ret_list = []
        for s in s_read:
            cs = res[s]
            ret_list.append(cs)
            self.active_connections.remove(cs)

        return ret_list

    def add_active_connections(self, connections: Iterable[ClientSocket]) -> None:
        for cs in connections:
            self.active_connections.add(cs)

    def close_connections(self, connections: Iterable[ClientSocket]) -> int:
        # FIXME: connection must be present in accepted connections and not present in active connections
        no_closed = 0
        for cs in connections:
            self.accepted_connections.remove(cs)
            cs.close()
            no_closed += 1

        if no_closed > 0:
            self.no_saturated_iterations = 0
        elif len(self.accepted_connections) == self.max_concurrent_connections:
            self.no_saturated_iterations += 1

        return no_closed

    def shutdown(self) -> None:
        # FIXME: unreliable, "best effort" error handling - 500 Internal Server Error
        self._close_with_error_responses(
            self.active_connections, ErrorResponses.http_internal_server_error()
        )
        self.server_s.close()
