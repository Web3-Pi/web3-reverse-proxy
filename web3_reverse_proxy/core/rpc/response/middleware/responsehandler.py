from web3_reverse_proxy.core.interfaces.rpcresponse import RPCResponseHandler
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket


class DefaultRPCResponseHandler(RPCResponseHandler):

    def __init__(self):
        pass

    def handle_response(self, cs: ClientSocket, response: RPCResponse) -> bool:
        assert cs.is_ready_write()

        try:
            cs.send_all(response.data)
        except IOError:
            return False
        except Exception:
            raise

        return True
