from threading import Lock

from web3pi_proxy.core.sockets.clientsocket import ClientSocket


class ClientSocketPoolEntry:
    def __init__(self, cs: ClientSocket):
        self.cs = cs
        self.prev = None
        self.next = None
        self.in_use = False


class ClientSocketPool:
    """
    Lightweight pool.
    Does not open or close client sockets, only bookkeeping.
    The pool has the structure of dict: file descriptor -> client socket (ClientSocketPoolEntry).
    Client sockets statuses are in_use or pending (in_use == False).
    Pending client sockets are additionally kept in linked list ordered by last usage starting from recent:
    head, tail and size are the attributes for the linked list.
    Thread-safe.
    But a caller must ensure conditions for each call.
    """

    def __init__(self):
        self.all_client_connections = {}
        self.head = None
        self.tail = None
        self.size = 0
        self.lock = Lock()

    def add_cs_pending(self, cs: ClientSocket):
        """Adds a new client socket to the pool, in pending status"""
        # assert all_client_connections.get(cs.socket.fileno()) is None
        with self.lock:
            entry = ClientSocketPoolEntry(cs)
            self.all_client_connections[cs.socket.fileno()] = entry
            if self.head is None:  # and self.tail is None
                self.tail = entry
            else:
                self.head.prev = entry
            self.head = entry
            self.size = self.size + 1

    def get_cs_and_set_in_use(self, fd: int) -> ClientSocket:
        """Searches for a client socket, it must be in pending status, is changed to in_use status and returned"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == False
        with self.lock:
            entry: ClientSocketPoolEntry = self.all_client_connections[fd]
            entry.in_use = True
            if entry.prev is None and entry.next is None:
                self.head = None
                self.tail = None
            elif entry.prev is None:  # and entry.next is not None
                self.head = entry.next
                self.head.prev = None
            elif entry.next is None:  # and entry.prev is not None
                self.tail = entry.prev
                self.tail.next = None
            else:
                entry.prev.next = entry.next
                entry.next.prev = entry.prev
            self.size = self.size - 1
            return entry.cs

    def set_cs_pending(self, fd: int):
        """Changes the status of a client socket to pending - it must be in_use beforehand"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == True
        with self.lock:
            entry: ClientSocketPoolEntry = self.all_client_connections[fd]
            entry.in_use = False
            entry.prev = None
            if self.head is None:  # and self.tail is None
                self.tail = entry
            else:
                self.head.prev = entry
            self.head = entry
            self.size = self.size + 1

    def del_cs_in_use(self, fd: int):
        """Removes a client socket from the pool - it must be in_use beforehand"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == True
        with self.lock:
            del self.all_client_connections[fd]

    def pop_cs_pending_from_tail(self) -> ClientSocket:
        with self.lock:
            tail_entry = self.tail
            self.tail = tail_entry.prev
            self.size = self.size - 1
            del self.all_client_connections[tail_entry.cs.socket.fileno()]
            return tail_entry.cs

    def get_size(self) -> int:
        """Returns the size of the list of pending cs"""
        return self.size

    def iterate_cs_pending(self):
        """Iterates the linked list of pending cs, from the tail to the head - from the last used to recently"""
        with self.lock:
            next_entry = self.tail
            while next_entry:
                entry = next_entry
                next_entry = (
                    entry.prev
                )  # entry.prev may be changed at yield, so there is the helper var next_entry
                yield entry
