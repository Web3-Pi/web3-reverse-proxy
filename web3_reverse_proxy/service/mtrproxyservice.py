from config.conf import ADMIN_LISTEN_PORT
from service.providers.upnpserviceprovider import UPnPServiceProvider
from service.tempimpl.mtproxy import Web3RPCProxyHackMT


class HackMultiThreadedRPCProxyService:

    def __init__(self) -> None:
        pass

    def run_forever(self, proxy_port: int, endpoint: str, endpoint_port: int, num_workers: int) -> None:
        upnp_service = UPnPServiceProvider.create_basic_upnp_service(proxy_port, ADMIN_LISTEN_PORT)
        upnp_service.try_init_upnp()

        proxy_server = Web3RPCProxyHackMT(proxy_port, endpoint, endpoint_port, num_workers)

        proxy_server.run_forever()
        upnp_service.close_upnp()
