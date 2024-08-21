from __future__ import annotations

from dataclasses import dataclass

import urllib3.util


@dataclass
class EndpointConnectionDescriptor:
    host: str
    port: int
    auth_key: str
    is_ssl: bool
    url: str
    extras: dict

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

        return EndpointConnectionDescriptor(host, int(port), auth_key, is_ssl, url, dict())

    @classmethod
    def from_dict(cls, conf: dict) -> EndpointConnectionDescriptor | None:
        url: str = conf["url"]
        conn_descr = cls.from_url(url)
        if not conn_descr:
            return None
        conn_descr.extras = conf.copy()
        del conn_descr.extras["name"]
        del conn_descr.extras["url"]
        return conn_descr
