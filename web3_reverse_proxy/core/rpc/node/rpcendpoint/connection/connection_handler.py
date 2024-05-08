import abc
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver


class ConnectionHandler(abc.ABC):
    def release(self) -> None:
        pass

    def get_sender(self) -> RequestSender:
        pass

    def get_receiver(self) -> ResponseReceiver:
        pass
