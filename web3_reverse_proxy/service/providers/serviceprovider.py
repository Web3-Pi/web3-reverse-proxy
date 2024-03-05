from typing import List, Tuple

from web3_reverse_proxy.config.conf import ETH_ENDPOINTS
from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler, LoadBalancer
from web3_reverse_proxy.core.interfaces.rpcresponse import RPCResponseHandler
from web3_reverse_proxy.core.proxy import Web3RPCProxy
from web3_reverse_proxy.core.rpc.node.rpcendpointhandlers.loadbalancers import simpleloadbalancers
from web3_reverse_proxy.core.rpc.request.middleware.requestmiddlewaredescr import RequestMiddlewareDescr

from web3_reverse_proxy.service.factories.endpointshandlermiddlewarefactory import RPCEndpointsHandlerMiddlewareFactory
from web3_reverse_proxy.service.factories.requestmiddlewarefactory import RPCRequestMiddlewareFactory
from web3_reverse_proxy.service.factories.responsemiddlewarefactory import RPCResponseMiddlewareFactory
from web3_reverse_proxy.service.http.adminserver import AdminServerRequestHandler, AdminHTTPServerThread
from web3_reverse_proxy.state.statemanager import SampleStateManager


class ServiceComponentsProvider:

    @classmethod
    def configure_default_reader_middlewares(cls, ssm: SampleStateManager) -> RequestMiddlewareDescr:
        cli = ssm.get_client_permissions_instance()
        call = ssm.get_call_permissions_instance()

        return RPCRequestMiddlewareFactory.create_default_descr(cli, call)

    @classmethod
    def create_default_endpoint_handler(cls, ssm: SampleStateManager, name: str, url: str) -> EndpointsHandler:
        updater = ssm.get_service_state_updater_instance()

        return RPCEndpointsHandlerMiddlewareFactory.create_pass_through(url, name, updater)

    @classmethod
    def create_default_multi_threaded_endpoint_handler(
        cls,
        endpoint_config: List[Tuple[str, str]],
        ssm:SampleStateManager,
    ):
        updater = ssm.get_service_state_updater_instance()

        return RPCEndpointsHandlerMiddlewareFactory.create_multi_thread(
            endpoint_config,
            updater,
            simpleloadbalancers.PriorityLoadBalancer,
        )

    @classmethod
    def create_default_response_handler(cls) -> RPCResponseHandler:
        return RPCResponseMiddlewareFactory.create_default_response_handler()

    @classmethod
    def create_web3_rpc_proxy(cls, ssm: SampleStateManager, handler: EndpointsHandler, proxy_port) -> Web3RPCProxy:
        # Create default components
        middlewares = cls.configure_default_reader_middlewares(ssm)
        endpoints_handler = handler
        response_handler = cls.create_default_response_handler()

        # Create proxy (do not launch it yet)
        proxy = Web3RPCProxy(proxy_port, middlewares, endpoints_handler, response_handler)

        # Pass proxy stats to StateManager, so that it may be queried
        ssm.register_proxy_stats(proxy.stats)

        # Pass endpoint data, so that it can be queried
        ssm.register_endpoints(endpoints_handler.get_endpoints())

        return proxy

    @classmethod
    def create_default_web3_rpc_proxy(cls, ssm: SampleStateManager, proxy_listen_port) -> Web3RPCProxy:
        # Create default components
        endpoint_handler = cls.create_default_multi_threaded_endpoint_handler(ETH_ENDPOINTS, ssm)

        return cls.create_web3_rpc_proxy(ssm, endpoint_handler, proxy_listen_port)

    @classmethod
    def create_admin_http_server_thread(cls, state_manager: SampleStateManager, listen_port):
        admin = state_manager.get_admin_instance()

        return AdminHTTPServerThread(admin, ("", listen_port), AdminServerRequestHandler)
