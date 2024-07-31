from contextlib import redirect_stdout
from io import StringIO

from web3pi_proxy.config.conf import (Config, ProxyMode)
from web3pi_proxy.service.ioredirect.stdoutcapture import StdOutCaptureStreamTee
from web3pi_proxy.service.providers.serviceprovider import (
    ServiceComponentsProvider,
)
from web3pi_proxy.service.providers.db_statemanagerprovider import (
    DbStateManagerProvider,
)
from web3pi_proxy.service.providers.upnpserviceprovider import UPnPServiceProvider


class DefaultRPCProxyService:

    def __init__(self, console_buffer: StringIO):
        self.__print_pre_init_info()

        self.state_manager = DbStateManagerProvider.create_state_manager(console_buffer)

        if Config.MODE == ProxyMode.DEV:
            self._init_test_accounts(self.state_manager.admin)

    @classmethod
    def __print_pre_init_info(cls):
        print(f"Starting {Config.SERVICE_NAME}, version {Config.SERVICE_VER}")

    @classmethod
    def _init_test_accounts(cls, admin):
        print("Default user registration flag set, registering users:")
        if not admin.is_user_registered("aaa"):
            admin.register_user_flat("aaa", 100000000, 1500 * 1024**3, 0, None)
            print(
                f"  Adding user: aaa, free calls: 100000000, free bytes: {1500 * 1024 ** 3:11}, priority: 0"
            )

        if not admin.is_user_registered("bbb"):
            admin.register_user_flat("bbb", 1000000, 2 * 1024**3, 1, None)
            print(
                f"  Adding user: bbb, free calls: 1000000, free bytes: {2 * 1024 ** 3:11}, priority: 1"
            )

        if not admin.is_user_registered("ccc"):
            admin.register_user_flat("ccc", 1000000, 1 * 1024**3, 2, None)
            print(
                f"  Adding user: ccc, free calls: 1000000, free bytes: {1 * 1024 ** 3:11}, priority: 2"
            )

    def run_forever(
        self,
        proxy_port=Config.PROXY_LISTEN_PORT,
        admin_port=Config.ADMIN_LISTEN_PORT,
        num_proxy_workers=Config.NUM_PROXY_WORKERS,
    ):
        upnp_service = UPnPServiceProvider.create_basic_upnp_service(
            proxy_port, admin_port
        )
        upnp_service.try_init_upnp()

        admin_thread = ServiceComponentsProvider.create_admin_http_server_thread(
            self.state_manager, admin_port
        )
        proxy_server = ServiceComponentsProvider.create_default_web3_rpc_proxy(
            self.state_manager, proxy_port, num_proxy_workers
        )

        admin_thread.start()
        proxy_server.run_forever()

        upnp_service.close_upnp()

        admin_thread.shutdown()

        DbStateManagerProvider.close_state_manager(self.state_manager)

    @classmethod
    def launch_service(
        cls,
        proxy_port=Config.PROXY_LISTEN_PORT,
        admin_port=Config.ADMIN_LISTEN_PORT,
        num_proxy_workers=Config.NUM_PROXY_WORKERS,
    ):
        with redirect_stdout(StdOutCaptureStreamTee()) as new_stdout:
            service = DefaultRPCProxyService(new_stdout)
            service.run_forever(proxy_port, admin_port, num_proxy_workers)
