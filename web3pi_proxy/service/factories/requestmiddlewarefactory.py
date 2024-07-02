from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.rpc.request.middleware.defaultmiddlewares.authenticator import (
    AuthRequestReader,
)
from web3pi_proxy.core.rpc.request.middleware.defaultmiddlewares.methodvalidator import (
    AcceptMethodRequestReader,
)
from web3pi_proxy.core.rpc.request.middleware.defaultmiddlewares.requestreader import (
    RequestReader,
)
from web3pi_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator import (
    AcceptJSONRPCContentReader,
)
from web3pi_proxy.core.rpc.request.middleware.requestmiddlewaredescr import (
    RequestMiddlewareDescr,
)
from web3pi_proxy.interfaces.permissions import CallPermissions, ClientPermissions


class RPCRequestMiddlewareFactory:

    @classmethod
    def create_from_request_middleware_descr(
        cls, descr: RequestMiddlewareDescr
    ) -> RequestReaderMiddleware:
        return descr.instantiate()

    @classmethod
    def create_default_descr(
        cls, cli: ClientPermissions, call: CallPermissions
    ) -> RequestMiddlewareDescr:
        md = RequestMiddlewareDescr()

        md.append(RequestReader)
        md.append(AuthRequestReader, cli)
        md.append(AcceptJSONRPCContentReader)
        md.append(AcceptMethodRequestReader, call)

        return md

    @classmethod
    def create_default_request_reader(
        cls, cli: ClientPermissions, call: CallPermissions
    ) -> RequestReaderMiddleware:
        descr = cls.create_default_descr(cli, call)

        return cls.create_from_request_middleware_descr(descr)
