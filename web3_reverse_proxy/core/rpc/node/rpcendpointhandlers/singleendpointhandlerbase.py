from abc import ABC
from typing import Iterable

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.interfaces.servicestate import StateUpdater

from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint


class SingleEndpointHandlerBase(EndpointsHandler, ABC):

    def __init__(self, name: str, conn_descr: EndpointConnectionDescriptor, state_updater: StateUpdater) -> None:
        self.endpoint = RPCEndpoint.create(name, conn_descr, state_updater)

    def close(self):
        self.endpoint.close()

    def get_endpoints(self) -> Iterable[RPCEndpoint]:
        return [self.endpoint]
