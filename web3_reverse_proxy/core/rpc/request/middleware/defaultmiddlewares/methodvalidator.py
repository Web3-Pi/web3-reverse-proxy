from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.interfaces.permissions import CallPermissions


class AcceptMethodRequestReader(RequestReaderMiddleware):

    def __init__(self, next_reader: RequestReaderMiddleware, call_permissions: CallPermissions):
        self.call_acceptor = call_permissions
        self.next_reader = next_reader

    def read_request(self, cs: ClientSocket, req: RPCRequest) -> RequestReaderMiddleware.ReturnType:
        if not self.call_acceptor.is_allowed(req.user_api_key, req.method):
            return self.failure(ErrorResponses.forbidden_payment_required(req.id), req)

        user_priority = self.call_acceptor.get_call_priority(req.user_api_key, req.method)
        req.priority = user_priority

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

        return self.success(req)

    def __str__(self):
        if self.next_reader:
            return f"AcceptMethod -> {self.next_reader}"
        else:
            return "AcceptMethod"
