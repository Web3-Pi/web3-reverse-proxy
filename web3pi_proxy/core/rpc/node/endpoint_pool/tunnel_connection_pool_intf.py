import socket


class TunnelConnectionPoolIntf:
    """Added to resolve the circular dependencies"""
    tunnel_proxy_establish_port: int

    def new_tunnel_service_socket(self, tunnel_service_socket: socket):
        pass
