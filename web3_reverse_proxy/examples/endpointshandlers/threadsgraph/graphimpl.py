from __future__ import annotations

from queue import Queue
from threading import Thread
from typing import Callable


class Queues:

    IN_0 = 0
    IN_1 = 1
    IN_2 = 2
    IN_3 = 3

    OUT_0 = 4
    OUT_1 = 5
    OUT_2 = 6
    OUT_3 = 7
    OUT_4 = 8


class ThreadsGraph:

    def __init__(self):
        self.queues = {}
        self.threads = []

    def get_queue(self, queue_id: int) -> Queue:
        if queue_id not in self.queues:
            self.queues[queue_id] = Queue()

        return self.queues[queue_id]

    def add_processing_thread(
        self, fun: Callable, input_queue: int, output_queue: int, *args
    ) -> None:
        assert input_queue != output_queue

        input_queue = self.get_queue(input_queue)
        output_queue = self.get_queue(output_queue)

        th = Thread(target=fun, args=(input_queue, output_queue, *args))
        th.daemon = True
        th.start()

        self.threads.append(th)

    @classmethod
    def create(cls) -> ThreadsGraph:
        return ThreadsGraph()
