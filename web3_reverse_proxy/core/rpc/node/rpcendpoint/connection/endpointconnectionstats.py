import time


class EndpointConnectionStats:

    def __init__(self):
        self._started_at = time.time()

        self._no_bytes_sent = 0
        self._no_bytes_received = 0
        self._no_requests_handled = 0

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

    def update(self, req_data: bytearray, resp_data: bytearray) -> None:
        self._no_requests_handled += 1
        self._no_bytes_sent += len(resp_data)
        self._no_bytes_received += len(req_data)

    def to_dict(self):
        return {
            'started_at_timestamp': self.started_at,
            'req_no': self.no_requests_handled,
            'bytes_sent': self.no_bytes_sent,
            'bytes_received': self.no_bytes_received
        }
