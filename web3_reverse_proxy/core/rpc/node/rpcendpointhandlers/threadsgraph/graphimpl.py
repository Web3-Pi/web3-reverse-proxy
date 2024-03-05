from __future__ import annotations

from collections import namedtuple
from queue import Queue
from threading import Thread
from typing import Callable


class Queues:

    _IN_PREFIX = "IN_"
    _OUT_PREFIX = "OUT_"

    @classmethod
    def create(self, num_in_queues: int, num_out_queues: int) -> None:

        self.in_queues = {}
        self.out_queues = {}

        in_labels = [self._IN_PREFIX + str(in_index) for in_index in range(num_in_queues)]
        out_labels = [self._OUT_PREFIX + str(out_index) for out_index in range(num_out_queues)]

        QueuesTuple = namedtuple("QueuesTuple", in_labels + out_labels)
        return QueuesTuple(*[index for index in range(num_in_queues + num_out_queues)])


class ThreadsGraph:

    def __init__(self):
        self.queues = {}
        self.threads = []

    def get_queue(self, queue_id: int) -> Queue:
        if queue_id not in self.queues:
            self.queues[queue_id] = Queue()

        return self.queues[queue_id]

    def add_processing_thread(self, fun: Callable, input_queue: int, output_queue: int, *args) -> None:
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
