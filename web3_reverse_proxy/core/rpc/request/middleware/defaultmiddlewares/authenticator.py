from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.utilhttp.errors import ErrorResponses
from web3_reverse_proxy.interfaces.permissions import ClientPermissions


class AuthRequestReader(RequestReaderMiddleware):

    def __init__(
        self,
        next_reader: RequestReaderMiddleware,
        client_permissions: ClientPermissions,
    ):
        self.auth = client_permissions
        self.next_reader = next_reader

    def read_request(
        self, cs: ClientSocket, req: RPCRequest
    ) -> RequestReaderMiddleware.ReturnType:
        if not self.auth.is_authorized(req.user_api_key):
            return self.failure(ErrorResponses.unauthorized_invalid_API_key(), req)

        return self.next_reader.read_request(cs, req)

    def __str__(self):
        return f"Auth -> {self.next_reader}"
