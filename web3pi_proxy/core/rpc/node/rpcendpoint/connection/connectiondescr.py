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

        return EndpointConnectionDescriptor(host, int(port), auth_key, is_ssl, url)
