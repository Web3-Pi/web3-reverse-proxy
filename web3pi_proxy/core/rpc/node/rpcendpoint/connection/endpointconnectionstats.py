import time
from threading import Lock


class EndpointConnectionStats:
    _started_at: float
    _no_bytes_sent: int
    _no_bytes_received: int
    _no_requests_handled: int

    def __init__(self):
        self._started_at = time.time()

        self._no_bytes_sent = 0
        self._no_bytes_received = 0
        self._no_requests_handled = 0
        self._no_errors = 0
        self._no_verification_errors = 0

        self.__lock = Lock()

    @property
    def started_at(self):
        return self._started_at

    @property
    def no_bytes_sent(self):
        return self._no_bytes_sent

    @property
    def no_bytes_received(self):
        return self._no_bytes_received

    @property
    def no_requests_handled(self):
        return self._no_requests_handled

    @property
    def no_errors(self):
        return self._no_errors

    @property
    def no_verification_errors(self):
        return self._no_verification_errors

    def _update(
        self, no_bytes_received: int, no_bytes_sent: int, no_requests_handled: int, no_errors: int = 0, no_verification_errors: int = 0
    ) -> None:
        with self.__lock:
            self._no_requests_handled += no_requests_handled
            self._no_bytes_sent += no_bytes_sent
            self._no_bytes_received += no_bytes_received
            self._no_errors += no_errors
            self._no_verification_errors += no_verification_errors

    def update_errors(self, no_errors: int) -> None:
        if no_errors:
            self._update(0, 0, 1, no_errors)

    def update_verification_errors(self, no_verification_errors: int) -> None:
        if no_verification_errors:
            self._update(0, 0, 1, 0, no_verification_errors)

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
            "errors_no": self._no_errors,
            "verification_errors_no": self._no_verification_errors,
        }
