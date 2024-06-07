import time
from threading import Lock


class EndpointConnectionStats:

    def __init__(self):
        self._started_at = time.time()

        self._no_bytes_sent = 0
        self._no_bytes_received = 0
        self._no_requests_handled = 0

        self.__lock = Lock()

    def __get_started_at(self):
        return self._started_at

    def __get_no_bytes_sent(self):
        return self._no_bytes_sent

    def __get_no_bytes_received(self):
        return self._no_bytes_received

    def __get_no_requests_handled(self):
        return self._no_requests_handled

    started_at = property(__get_started_at)
    no_bytes_sent = property(__get_no_bytes_sent)
    no_bytes_received = property(__get_no_bytes_received)
    no_requests_handled = property(__get_no_requests_handled)

    def _update(
        self, no_bytes_received: int, no_bytes_sent: int, no_requests_handled: int
    ) -> None:
        with self.__lock:
            self._no_requests_handled += no_requests_handled
            self._no_bytes_sent += no_bytes_sent
            self._no_bytes_received += no_bytes_received

    def update_request_bytes(self, req_data: bytearray) -> None:
        no_req_bytes = len(req_data)
        if no_req_bytes:
            self._update(no_req_bytes, 0, 1)

    def update_response_bytes(self, res_data: bytearray) -> None:
        no_res_bytes = len(res_data)
        if no_res_bytes:
            self._update(0, no_res_bytes, 0)

    def to_dict(self):
        return {
            "started_at_timestamp": self.started_at,
            "req_no": self.no_requests_handled,
            "bytes_sent": self.no_bytes_sent,
            "bytes_received": self.no_bytes_received,
        }
