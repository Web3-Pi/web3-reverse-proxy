from typing import List

from web3_reverse_proxy.config.conf import Config
from web3_reverse_proxy.core.interfaces.rpcresponse import RPCResponseHandler
from web3_reverse_proxy.core.proxy import Web3RPCProxy
from web3_reverse_proxy.core.rpc.node.endpoint_pool import load_balancers
from web3_reverse_proxy.core.rpc.node.endpoint_pool.pool_manager import (
    EndpointConnectionPoolManager,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import (
    RequestMiddlewareDescr,
)
from web3_reverse_proxy.service.factories.requestmiddlewarefactory import (
    RPCRequestMiddlewareFactory,
)
from web3_reverse_proxy.service.factories.responsemiddlewarefactory import (
    RPCResponseMiddlewareFactory,
)
from web3_reverse_proxy.service.http.adminserver import (
    AdminHTTPServerThread,
    AdminServerRequestHandler,
)
from web3_reverse_proxy.state.statemanager import SampleStateManager


class ServiceComponentsProvider:

    @classmethod
    def configure_default_reader_middlewares(
        cls, ssm: SampleStateManager
    ) -> RequestMiddlewareDescr:
        cli = ssm.get_client_permissions_instance()
        call = ssm.get_call_permissions_instance()

        return RPCRequestMiddlewareFactory.create_default_descr(cli, call)

    @classmethod
    def create_default_connection_pool(cls, endpoint_config: List[dict]):
        descriptors = [
            (
                entrypoint["name"],
                EndpointConnectionDescriptor.from_url(entrypoint["url"]),
            )
            for entrypoint in endpoint_config
        ]
        # TODO: Settle on most suitable place for plugging in load balancer for interchangeability
        load_balancer = load_balancers.RandomLoadBalancer()
        return EndpointConnectionPoolManager(descriptors, load_balancer)

    @classmethod
    def create_default_response_handler(cls) -> RPCResponseHandler:
        return RPCResponseMiddlewareFactory.create_default_response_handler()

    @classmethod
    def create_web3_rpc_proxy(
        cls,
        ssm: SampleStateManager,
        connection_pool: EndpointConnectionPoolManager,
        proxy_port,
        num_proxy_workers: int,
    ) -> Web3RPCProxy:
        # Create default components
        middlewares = cls.configure_default_reader_middlewares(ssm)

        # Create proxy (do not launch it yet)
        proxy = Web3RPCProxy(
            proxy_port,
            num_proxy_workers,
            middlewares,
            connection_pool,
            ssm.get_service_state_updater_instance(),
        )

        # Pass proxy stats to StateManager, so that it may be queried
        # ssm.register_proxy_stats(proxy.stats)

        # Pass endpoint data, so that it can be queried
        ssm.create_endpoint_manager(connection_pool)

        return proxy

    @classmethod
    def create_default_web3_rpc_proxy(
        cls, ssm: SampleStateManager, proxy_listen_port, num_proxy_workers: int
    ) -> Web3RPCProxy:
        # Create default components
        connection_pool = cls.create_default_connection_pool(Config.ETH_ENDPOINTS)

        return cls.create_web3_rpc_proxy(
            ssm, connection_pool, proxy_listen_port, num_proxy_workers
        )

    @classmethod
    def create_admin_http_server_thread(
        cls, state_manager: SampleStateManager, listen_port
    ):
        admin = state_manager.get_admin_instance()

        return AdminHTTPServerThread(
            admin, ("", listen_port), AdminServerRequestHandler
        )
