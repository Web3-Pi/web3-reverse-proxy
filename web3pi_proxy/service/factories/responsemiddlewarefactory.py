from web3pi_proxy.core.rpc.response.middleware.responsehandler import (
    DefaultRPCResponseHandler,
)


class RPCResponseMiddlewareFactory:

    @classmethod
    def create_default_response_handler(cls):
        return DefaultRPCResponseHandler()
