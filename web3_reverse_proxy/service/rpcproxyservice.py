from contextlib import redirect_stdout
from io import StringIO

from service.mtrproxyservice import HackMultiThreadedRPCProxyService
from web3_reverse_proxy.config.conf import SERVICE_NAME, PROXY_LISTEN_PORT, SERVICE_VER, ADMIN_LISTEN_PORT, \
    FORCE_REGISTER_DEFAULT_USERS
from web3_reverse_proxy.service.ioredirect.stdoutcapture import StdOutCaptureStreamTee
from web3_reverse_proxy.service.providers.statemanagerprovider import StateManagerProvider

from web3_reverse_proxy.service.providers.serviceprovider import ServiceComponentsProvider
from web3_reverse_proxy.service.providers.upnpserviceprovider import UPnPServiceProvider


class DefaultRPCProxyService:

    def __init__(self, console_buffer: StringIO):
        self.__print_pre_init_info()

        self.state_manager = StateManagerProvider.create_state_manager(console_buffer)

        self._init_test_accounts(self.state_manager.admin_impl)

    @classmethod
    def __print_pre_init_info(cls):
        print(f"Starting {SERVICE_NAME}, version {SERVICE_VER}")

    @classmethod
    def _init_test_accounts(cls, admin):
        # FIXME: default users added for testing purposes
        if FORCE_REGISTER_DEFAULT_USERS:
            print("Default user registration flag set, registering users:")
            if not admin.is_user_registered("aaa"):
                admin.register_user_flat("aaa", 1000000, 15 * 1024 ** 3, 0)
                print(f"  Adding user: aaa, free calls: 1000000, free bytes: {15 * 1024 ** 3:11}, priority: 0")

            if not admin.is_user_registered("bbb"):
                admin.register_user_flat("bbb", 1000000, 2 * 1024 ** 3, 1)
                print(f"  Adding user: bbb, free calls: 1000000, free bytes: {2 * 1024 ** 3:11}, priority: 1")

            if not admin.is_user_registered("ccc"):
                admin.register_user_flat("ccc", 1000000, 1 * 1024 ** 3, 2)
                print(f"  Adding user: ccc, free calls: 1000000, free bytes: {1 * 1024 ** 3:11}, priority: 2")

    def run_forever(self, proxy_port=PROXY_LISTEN_PORT, admin_port=ADMIN_LISTEN_PORT):
        upnp_service = UPnPServiceProvider.create_basic_upnp_service(proxy_port, admin_port)
        upnp_service.try_init_upnp()

        admin_thread = ServiceComponentsProvider.create_admin_http_server_thread(self.state_manager, admin_port)
        proxy_server = ServiceComponentsProvider.create_default_web3_rpc_proxy(self.state_manager, proxy_port)

        admin_thread.start()
        proxy_server.run_forever()

        upnp_service.close_upnp()

        admin_thread.shutdown()

        StateManagerProvider.close_state_manager(self.state_manager)

    @classmethod
    def launch_service(cls, proxy_port=PROXY_LISTEN_PORT, admin_port=ADMIN_LISTEN_PORT):
        with redirect_stdout(StdOutCaptureStreamTee()) as new_stdout:
            service = DefaultRPCProxyService(new_stdout)
            service.run_forever(proxy_port, admin_port)

    @classmethod
    def launch_hack_mt_service(cls, proxy_port, endpoint: str, endpoint_port: int, num_workers: int) -> None:
        HackMultiThreadedRPCProxyService().run_forever(proxy_port, endpoint, endpoint_port, num_workers)
