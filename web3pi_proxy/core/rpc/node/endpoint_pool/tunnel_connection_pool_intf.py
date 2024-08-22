import socket


class TunnelConnectionPoolIntf:
    tunnel_proxy_establish_port: int

    def new_tunnel_service_socket(self, tunnel_service_socket: socket):
        pass
