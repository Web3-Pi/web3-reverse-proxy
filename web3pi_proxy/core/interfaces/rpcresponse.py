from abc import ABC, abstractmethod

from web3pi_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3pi_proxy.core.sockets.clientsocket import ClientSocket


class RPCResponseHandler(ABC):

    @abstractmethod
    def handle_response(self, cs: ClientSocket, response: RPCResponse) -> bool:
        pass
