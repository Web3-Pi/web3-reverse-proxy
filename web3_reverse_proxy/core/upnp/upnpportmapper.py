import socket
from typing import List

import upnpclient

from upnpclient import UPNPError
from upnpclient.soap import SOAPError


class BasicUPnPPortMapper:

    ACTION_ADD_PORT_MAPPING = "AddPortMapping"
    ACTION_DELETE_PORT_MAPPING = "DeletePortMapping"
    ACTION_GET_EXTERNAL_IP_ADDRESS = "GetExternalIPAddress"

    SERVICE_WAN_IP_CONN_1 = "WANIPConn1"

    REQUIRED_ACTIONS = [ACTION_ADD_PORT_MAPPING, ACTION_DELETE_PORT_MAPPING, ACTION_GET_EXTERNAL_IP_ADDRESS]

    def __init__(self):
        self.initialized = False
        self.local_ip = None
        self.device = None
        self.ext_ports = set()

    @classmethod
    def get_local_addr_ipv4(cls):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            # s.connect(('10.254.254.254', 1))
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def initialize(self, timeout: float) -> bool:
        assert not self.initialized

        devices = upnpclient.discover(timeout)

        for dev in devices:
            actions = set(a.name for a in dev.actions)
            services = set(s.name for s in dev.services)

            if self.SERVICE_WAN_IP_CONN_1 in services and all(ra in actions for ra in self.REQUIRED_ACTIONS):
                self.device = dev
                break

        self.local_ip = self.get_local_addr_ipv4()
        self.initialized = True

        return self.device is not None

    def is_upnp_available(self) -> bool:
        assert self.initialized

        return self.device is not None

    def get_actions(self):
        assert self.is_upnp_available()

        return self.device.actions

    def add_simple_mapping_rule(self, port: int, rule_descr: str, lease_duration: int) -> bool:
        assert self.is_upnp_available()

        d = self.device
        try:
            r = d.WANIPConn1.AddPortMapping(NewRemoteHost='',
                                            NewExternalPort=port,
                                            NewProtocol='TCP',
                                            NewInternalPort=port,
                                            NewInternalClient=self.local_ip,
                                            NewEnabled='1',
                                            NewPortMappingDescription=rule_descr,
                                            NewLeaseDuration=lease_duration)
            assert len(r) == 0
        except (UPNPError, SOAPError) as ex:
            return False

        self.ext_ports.add(port)

        return True

    def delete_mapping_rule(self, port: int) -> bool:
        assert self.is_upnp_available()

        d = self.device
        try:
            r = d.WANIPConn1.DeletePortMapping(NewRemoteHost='',
                                               NewExternalPort=port,
                                               NewProtocol='TCP')
            assert len(r) == 0
        except (UPNPError, SOAPError):
            return False

        if port in self.ext_ports:
            self.ext_ports.remove(port)

        return True

    def get_external_ip_address(self):
        assert self.is_upnp_available()

        return self.device.WANIPConn1.GetExternalIPAddress()['NewExternalIPAddress']

    def get_status(self):
        assert self.is_upnp_available()

        return self.device.WANIPConn1.GetStatusInfo()

    def add_multiple_mappings(self, ports: List[int], rules_descr: List[str], lease_duration: int) -> bool:
        assert len(ports) == len(rules_descr)

        res = True
        for port, rule in zip(ports, rules_descr):
            res = res and self.add_simple_mapping_rule(port, rule, lease_duration)

            if not res:
                break

        if not res:
            self.delete_all_created_mappings()

        return res

    def delete_all_created_mappings(self) -> None:
        ports = list(self.ext_ports)

        for port in ports:
            self.delete_mapping_rule(port)
