from typing import List, Tuple

from core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.interfaces.servicestate import StateUpdater

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer

from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.defaultendpointhandler import SingleEndpointHandler
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.threadedendpointhandler import ThreadedEndpointHandler


class RPCEndpointsHandlerMiddlewareFactory:

    @classmethod
    def create_pass_through(cls, url: str, name: str, state_updater: StateUpdater) -> EndpointsHandler:
        connection_descr = EndpointConnectionDescriptor.from_url(url)
        assert connection_descr is not None

        return SingleEndpointHandler(name, connection_descr, state_updater)

    @classmethod
    def create_passthrough_rpc_endpoint(cls, url: str, name: str, state_updater: StateUpdater) -> RPCEndpoint:
        connection_descr = EndpointConnectionDescriptor.from_url(url)
        assert connection_descr is not None

        return RPCEndpoint.create(name, connection_descr, state_updater)

    @classmethod
    def create_multi_thread(cls, endpoint_config: List[Tuple[str, str]], state_updater: StateUpdater, load_balancer: LoadBalancer) -> EndpointsHandler:
        descriptors = [(name, EndpointConnectionDescriptor.from_url(url)) for name, url in endpoint_config]

        return ThreadedEndpointHandler(descriptors, state_updater, load_balancer)
