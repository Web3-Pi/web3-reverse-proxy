import time

from web3pi_proxy.config.conf import Config


class RPCProxyStats:

    def __init__(
        self,
        stats_print_delta: int = Config.STATS_UPDATE_DELTA,
        stats_delay: int = Config.STATS_UPDATE_MIN_DELAY,
    ) -> None:
        self.prev_stats_print_marker = 0
        self.last_update = time.time()

        self.stats_print_delta = stats_print_delta
        self.stats_update_min_delay = stats_delay

        self.clients_num = 0
        self.request_num = 0
        self.disconnected_num = 0

    def to_dict(self):
        return {
            "clients_num": self.clients_num,
            "disconnected_num": self.disconnected_num,
            "requests_num": self.request_num,
        }

    def update(
        self,
        no_new_clients: int,
        no_processed_requests: int,
        no_disconnected_clients: int,
    ) -> None:
        self.clients_num += no_new_clients
        self.request_num += no_processed_requests
        self.disconnected_num += no_disconnected_clients

    def is_ready_to_update_display(self):
        time_cond = time.time() - self.last_update > self.stats_update_min_delay
        count_cond = (
            self.request_num + self.clients_num
        ) // self.stats_print_delta > self.prev_stats_print_marker

        return time_cond and count_cond

    def display_rudimentary_stats(self) -> None:
        self.prev_stats_print_marker = (
            self.request_num + self.clients_num
        ) // self.stats_print_delta
        self.last_update = time.time()

        print(
            f"\rProcessed {self.request_num} requests from {self.clients_num} connections "
            f"and disconnected {self.disconnected_num} clients",
            end="",
        )
