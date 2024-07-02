from web3pi_proxy.service.upnp.upnpservice import BasicUPnPService


class UPnPServiceProvider:

    @classmethod
    def create_basic_upnp_service(
        cls, proxy_port: int, admin_port: int
    ) -> BasicUPnPService:
        return BasicUPnPService(proxy_port, admin_port)
