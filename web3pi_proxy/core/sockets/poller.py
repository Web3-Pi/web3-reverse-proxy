import select
from typing import Protocol, List, Tuple, TypeAlias

POLLIN = 0x0001
POLLPRI = 0x0002
POLLOUT = 0x0004
POLLERR = 0x0008
POLLHUP = 0x0010
POLLNVAL = 0x0020


class HasFileno(Protocol):
    def fileno(self) -> int: ...


FileDescriptorLike: TypeAlias = int | HasFileno  # stable


class Poller(Protocol):
    def register(self, fd: FileDescriptorLike, eventmask: int) -> None:
        ...

    def unregister(self, fd: FileDescriptorLike) -> None:
        ...

    def modify(self, fd: FileDescriptorLike, eventmask: int) -> None:
        ...

    def poll(self, timeout: int = -1) -> List[Tuple[int, int]]:
        ...


def get_poller() -> Poller:
    try:
        return select.epoll()
    except AttributeError:
        return select.poll()
