from web3pi_proxy.config.conf import Config
from web3pi_proxy.core.upnp.ipgetter import my_public_ip
from web3pi_proxy.core.upnp.upnpportmapper import BasicUPnPPortMapper


class BasicUPnPService:

    def __init__(self, proxy_port: int, admin_port: int) -> None:
        self.upnp = None
        self.proxy_port = proxy_port
        self.admin_port = admin_port

    def try_init_upnp(self, timeout: float = Config.UPNP_DISCOVERY_TIMEOUT) -> bool:
        assert self.upnp is None

        ip = None
        res = False

        if Config.USE_UPNP:
            print("Initializing UPnP service")
            self.upnp = BasicUPnPPortMapper()
            self.upnp.initialize(timeout)

            print("UPnP service: Trying to map ports via UPnP")

            ports = [self.proxy_port, self.admin_port]
            rules = ["Web3 Proxy", "Proxy Admin"]
            res = self.upnp.add_multiple_mappings(ports, rules, Config.UPNP_LEASE_TIME)

            if not res:
                print("UPnP service: port forwarding -> FAILURE")
            else:
                print(
                    f"UPnP service: forwarded proxy port {self.proxy_port} and http admin port {self.admin_port}"
                )
                ip = self.upnp.get_external_ip_address()

        if ip is None:
            if Config.PUBLIC_SERVICE:
                ip = my_public_ip()
            else:
                ip = "127.0.0.1"

        print(f"Service bound to ip address: {ip}")

        return res

    def close_upnp(self):
        if Config.USE_UPNP:
            print("UPnP service: shutting down - closing all mapped ports")

            if self.upnp.is_upnp_available():
                self.upnp.delete_all_created_mappings()

            print("UPnP service: shutdown complete")
