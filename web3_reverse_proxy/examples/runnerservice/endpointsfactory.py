from typing import List, Tuple

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.examples.endpointshandlers.multiinfuraarchhandler import (
    MultiInfuraArchEndpointHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.multilocaldeviceqosloadbalancing import (
    MultiDeviceLocalLoadBalancingQoSHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.multilocalqosinverleave import (
    MultiEndpointLocalInterleaveQoSHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.multilocalqosloadbalancing import (
    MultiEndpointLocalLoadBalancingQoSHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.multilocalqosmethod import (
    MultiEndpointLocalMethodQoSHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.multiprioritycomplexhandler import (
    MultiPriorityComplexEndpointHandler,
)
from web3_reverse_proxy.examples.endpointshandlers.priorityendpointhandler import (
    PriorityEndpointHandler,
)
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class ExampleHandlerMiddlewareFactory:

    @classmethod
    def _conn_descr(cls, url: str) -> EndpointConnectionDescriptor:
        descr = EndpointConnectionDescriptor.from_url(url)
        assert descr is not None

        return descr

    @classmethod
    def create_single_endpoint_prio(
        cls,
        url: str,
        name: str,
        state_updater: StateUpdater,
        max_rate_1: float,
        max_rate_2: float,
    ) -> EndpointsHandler:
        descr = cls._conn_descr(url)
        return PriorityEndpointHandler.create_single_local_prio(
            name, descr, state_updater, max_rate_1, max_rate_2
        )

    @classmethod
    def create_multi_endpoint_method_qos(
        cls, url: str, name: str, state_updater: StateUpdater
    ):
        descr = cls._conn_descr(url)
        return MultiEndpointLocalMethodQoSHandler(name, descr, state_updater)

    @classmethod
    def create_multi_endpoint_interleave_qos(
        cls, url: str, name: str, state_updater: StateUpdater
    ):
        descr = cls._conn_descr(url)
        return MultiEndpointLocalInterleaveQoSHandler(name, descr, state_updater)

    @classmethod
    def create_multi_endpoint_load_balancing_qos(
        cls, url: str, name: str, state_updater: StateUpdater
    ):
        descr = cls._conn_descr(url)
        return MultiEndpointLocalLoadBalancingQoSHandler(name, descr, state_updater)

    @classmethod
    def create_multi_infura_endpoint_prio(
        cls,
        url_eth: str,
        name_eth: str,
        url_infura: str,
        name_infura: str,
        state_updater: StateUpdater,
        rate1: float,
        rate2: float,
    ):
        descr_eth = cls._conn_descr(url_eth)
        descr_inf = cls._conn_descr(url_infura)

        return PriorityEndpointHandler.create_multi_infura_prio(
            name_eth, descr_eth, name_infura, descr_inf, state_updater, rate1, rate2
        )

    @classmethod
    def create_multi_infura_complex_endpoint_prio(
        cls,
        url_eth: str,
        name_eth: str,
        url_infura: str,
        name_infura: str,
        state_updater: StateUpdater,
    ):
        descr_eth = cls._conn_descr(url_eth)
        descr_inf = cls._conn_descr(url_infura)

        return MultiPriorityComplexEndpointHandler.create(
            name_eth, descr_eth, name_infura, descr_inf, state_updater
        )

    @classmethod
    def create_multi_infura_arch_endpoint_prio(
        cls,
        url_eth: str,
        name_eth: str,
        url_infura: str,
        name_infura: str,
        state_updater: StateUpdater,
    ):
        descr_eth = cls._conn_descr(url_eth)
        descr_inf = cls._conn_descr(url_infura)

        return MultiInfuraArchEndpointHandler.create(
            name_eth, descr_eth, name_infura, descr_inf, state_updater
        )

    @classmethod
    def create_multi_device_load_balancing_qos(
        cls, endpoints: List[Tuple[str, str]], state_updater: StateUpdater
    ):
        descriptors = [(name, cls._conn_descr(addr)) for addr, name in endpoints]

        return MultiDeviceLocalLoadBalancingQoSHandler(descriptors, state_updater)
