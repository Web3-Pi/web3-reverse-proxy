from contextlib import redirect_stdout

from io import StringIO

from web3_reverse_proxy.config.conf import SERVICE_NAME, SERVICE_VER, PROXY_LISTEN_PORT, ADMIN_LISTEN_PORT

from web3_reverse_proxy.core.interfaces.rpcnode import EndpointsHandler

from web3_reverse_proxy.service.ioredirect.stdoutcapture import StdOutCaptureStreamTee

from web3_reverse_proxy.service.providers.serviceprovider import ServiceComponentsProvider
from web3_reverse_proxy.service.providers.statemanagerprovider import StateManagerProvider
from web3_reverse_proxy.service.providers.upnpserviceprovider import UPnPServiceProvider


class ExampleRunnerService:

    def __init__(self, console_buffer: StringIO):
        self.__print_pre_init_info()

        self.state_manager = StateManagerProvider.create_state_manager(console_buffer, skip_persistent_db=True)

        self._init_test_accounts(self.state_manager.admin_impl)

    def get_state_manager(self):
        return self.state_manager

    @classmethod
    def __print_pre_init_info(cls):
        print(f"Starting {SERVICE_NAME}, version {SERVICE_VER} - EXAMPLE MODE (pickle DB is not active)")

    @classmethod
    def _init_test_accounts(cls, admin):
        # FIXME: default users added for testing purposes
        if SERVICE_VER == "0.0.1":
            if not admin.is_user_registered("aaa"):
                admin.register_user_flat("aaa", 1000000, 15 * 1024 ** 3, 0)

            if not admin.is_user_registered("bbb"):
                admin.register_user_flat("bbb", 1000000, 2 * 1024 ** 3, 1)

            if not admin.is_user_registered("ccc"):
                admin.register_user_flat("ccc", 1000000, 1 * 1024 ** 3, 2)

    def run_forever(self, handler: EndpointsHandler):
        upnp_service = UPnPServiceProvider.create_basic_upnp_service(PROXY_LISTEN_PORT, ADMIN_LISTEN_PORT)
        upnp_service.try_init_upnp()

        admin_thread = ServiceComponentsProvider.create_admin_http_server_thread(self.state_manager, ADMIN_LISTEN_PORT)
        proxy_server = ServiceComponentsProvider.create_web3_rpc_proxy(self.state_manager, handler, PROXY_LISTEN_PORT)

        admin_thread.start()
        proxy_server.run_forever()

        upnp_service.close_upnp()

        admin_thread.shutdown()

        StateManagerProvider.close_state_manager(self.state_manager, skip_persistent_db=True)

    @classmethod
    def launch(cls, handler: EndpointsHandler):
        new_stdout = StdOutCaptureStreamTee()

        with redirect_stdout(new_stdout):
            service = ExampleRunnerService(new_stdout)
            service.run_forever(handler)
