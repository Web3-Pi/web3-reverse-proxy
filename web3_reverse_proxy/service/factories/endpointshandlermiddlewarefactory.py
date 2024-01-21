from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.interfaces.servicestate import StateUpdater

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler

from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.defaultendpointhandler import SingleEndpointHandler


class RPCEndpointsHandlerMiddlewareFactory:

    @classmethod
    def create_pass_through(cls, url: str, name: str, state_updater: StateUpdater) -> EndpointsHandler:
        connection_descr = EndpointConnectionDescriptor.from_url(url)
        assert connection_descr is not None

        return SingleEndpointHandler(name, connection_descr, state_updater)
