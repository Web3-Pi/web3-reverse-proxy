from abc import ABCMeta, abstractmethod


class ConnectionHandler(metaclass=ABCMeta):
    @abstractmethod
    def send(self) -> bytearray:
        pass

    @abstractmethod
    def receive(self) -> None:
        pass

    @abstractmethod
    def release(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
