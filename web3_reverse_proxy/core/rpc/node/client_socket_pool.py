from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


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
    Pending client sockets are additionally kept in linked list ordered by last usage starting from recent.
    Thread-safe.
    But a caller must ensure conditions for each call.
    """
    def __init__(self):
        self.all_client_connections = {}
        self.head = None
        self.tail = None

    def add_cs_pending(self, cs: ClientSocket):
        """ Adds a new client socket to the pool, in pending status"""
        # assert all_client_connections.get(cs.socket.fileno()) is None
        entry = ClientSocketPoolEntry(cs)
        self.all_client_connections[cs.socket.fileno()] = entry
        if self.head is None:  # and self.tail is None
            self.tail = entry
        else:
            self.head.prev = entry
        self.head = entry

    def get_cs_and_set_in_use(self, fd: int) -> ClientSocket:
        """ Searches for a client socket, it must be in pending status, is changed to in_use status and returned"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == False
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
        return entry.cs

    def set_cs_pending(self, fd: int):
        """ Changes the status of a client socket to pending - it must be in_use beforehand"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == True
        entry: ClientSocketPoolEntry = self.all_client_connections[fd]
        entry.in_use = False
        entry.prev = None
        if self.head is None:  # and self.tail is None
            self.tail = entry
        else:
            self.head.prev = entry
        self.head = entry

    def del_cs_in_use(self, fd: int):
        """ Removes a client socket from the pool - it must be in_use beforehand"""
        # assert all_client_connections.get(fd) is not None
        # assert all_client_connections[fd].in_use == True
        del self.all_client_connections[fd]
