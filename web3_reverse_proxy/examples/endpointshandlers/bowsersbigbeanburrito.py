from __future__ import annotations

from typing import List, Tuple

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint

from web3_reverse_proxy.examples.endpointshandlers.threadedhandlers.threadedendpointhandler import ThreadedEndpointHandler
from web3_reverse_proxy.examples.endpointshandlers.threadsgraph.graphimpl import Queues

from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class BowsersBigBeanBurritoHandler(ThreadedEndpointHandler):
    def __init__(self):
        super().__init__()

    @classmethod
    def create(cls, descriptors: List[Tuple[str, EndpointConnectionDescriptor]],
               state_updater: StateUpdater) -> BowsersBigBeanBurritoHandler:

        instance = BowsersBigBeanBurritoHandler()

        # # Endpoints are appended to the endpoints list in the order of adding consumers
        instance.add_request_consumer(Queues.IN_0, RPCEndpoint.create(descriptors[0][0] + " pt-0", descriptors[0][1], state_updater))
        instance.add_request_consumer(Queues.IN_1, RPCEndpoint.create(descriptors[1][0] + " pt-1", descriptors[1][1], state_updater))
        instance.add_request_consumer(Queues.IN_2, RPCEndpoint.create(descriptors[2][0] + " pt-2", descriptors[2][1], state_updater))

        return instance
