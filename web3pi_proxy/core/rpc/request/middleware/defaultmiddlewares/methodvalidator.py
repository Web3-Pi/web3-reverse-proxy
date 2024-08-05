from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.sockets.clientsocket import ClientSocket
from web3pi_proxy.core.utilhttp.errors import ErrorResponses
from web3pi_proxy.interfaces.permissions import CallPermissions
from web3pi_proxy.config.conf import (Config, ProxyMode)


class AcceptMethodRequestReader(RequestReaderMiddleware):

    def __init__(
        self, next_reader: RequestReaderMiddleware, call_permissions: CallPermissions
    ):
        self.call_acceptor = call_permissions
        self.next_reader = next_reader

    def read_request(
        self, cs: ClientSocket, req: RPCRequest
    ) -> RequestReaderMiddleware.ReturnType:
        if Config.MODE == ProxyMode.SIM:
            req.priority = 0
            req.constant_pool = None
        else:
            if not self.call_acceptor.is_allowed(req.user_api_key, req.method):
                return self.failure(ErrorResponses.forbidden_payment_required(req.id), req)

            user_priority = self.call_acceptor.get_call_priority(
                req.user_api_key, req.method
            )
            req.priority = user_priority
            user_constant_pool = self.call_acceptor.get_user_constant_pool(req.user_api_key)
            req.constant_pool = user_constant_pool

        if self.next_reader:
            return self.next_reader.read_request(cs, req)

        return self.success(req)

    def __str__(self):
        if self.next_reader:
            return f"AcceptMethod -> {self.next_reader}"
        else:
            return "AcceptMethod"
