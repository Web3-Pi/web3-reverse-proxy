from abc import ABC, abstractmethod

from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class RPCResponseHandler(ABC):

    @abstractmethod
    def handle_response(self, cs: ClientSocket, response: RPCResponse) -> bool:
        pass
