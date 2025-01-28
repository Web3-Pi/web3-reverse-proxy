from __future__ import annotations

import logging
from dataclasses import dataclass
import enum
import urllib3.util


class ConnectionType(enum.Enum):
    DIRECT = "DIRECT"
    TUNNEL = "TUNNEL"


@dataclass
class EndpointConnectionDescriptor:
    host: str
    port: int
    auth_key: str
    is_ssl: bool
    url: str
    extras: dict
    connection_type: ConnectionType

    @classmethod
    def from_url(cls, url) -> EndpointConnectionDescriptor | None:
        parsed = urllib3.util.parse_url(url)

        host = parsed.host
        port = parsed.port
        auth_key = parsed.path or ""
        is_ssl = parsed.scheme == "https" if parsed.scheme is not None else None

        if host is None:
            return None

        if len(auth_key) > 0:
            auth_key = auth_key[1:]

        if is_ssl is None:
            return None

        if port is None:
            if is_ssl:
                port = 443
            else:
                return None

        return EndpointConnectionDescriptor(host, int(port), "", is_ssl, url, dict(), ConnectionType.DIRECT)

    @classmethod
    def from_dict(cls, conf: dict) -> EndpointConnectionDescriptor | None:
        url: str = conf["url"]
        conn_descr = cls.from_url(url)
        if not conn_descr:
            raise Exception(f"Invalid url provided: {url}")
        connection_type: str = conf.get("connection_type")
        if connection_type:
            try:
                conn_descr.connection_type = ConnectionType(connection_type.upper())
            except ValueError:
                raise Exception(f"Unrecognized connection type {connection_type}")
        else:
            conn_descr.connection_type = ConnectionType.DIRECT
        conn_descr.extras = conf.copy()
        conn_descr.auth_key = conf.get("auth_key") or ""
        del conn_descr.extras["name"]
        del conn_descr.extras["url"]
        conn_descr.extras.pop("connection_type", None)
        print(f"Connection descriptor: {conn_descr}")
        return conn_descr
