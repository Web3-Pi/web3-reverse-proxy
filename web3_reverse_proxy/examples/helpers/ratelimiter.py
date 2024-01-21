import time


class RateLimiter:

    def __init__(self, max_rate: float):
        self.rate_delay = 1.0 / max_rate
        self.last_event_time = time.time() - self.rate_delay

    def wait(self):
        duration = time.time() - self.last_event_time

        if duration < self.rate_delay:
            time.sleep(self.rate_delay - duration)

        self.last_event_time = time.time()
