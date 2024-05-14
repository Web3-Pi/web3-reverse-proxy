from abc import ABCMeta, abstractmethod

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver


class ConnectionHandler(metaclass=ABCMeta):
    @abstractmethod
    def release(self) -> None:
        pass

    @abstractmethod
    def get_sender(self) -> RequestSender:
        pass

    @abstractmethod
    def get_receiver(self) -> ResponseReceiver:
        pass
