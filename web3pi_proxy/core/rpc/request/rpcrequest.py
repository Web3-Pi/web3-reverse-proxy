from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class RPCRequest:
    user_api_key: Optional[str] = None
    url_path: Optional[bytearray] = None
    headers: Optional[bytearray] = None
    content_len: int = -1
    content: Optional[bytearray] = None
    method: str = ""
    id: Optional[Union[int, str]] = None
    priority: int = 0
    constant_pool: Optional[str] = None
    last_queried_bytes: Optional[bytearray] = None
    keep_alive: bool = True
    http_method: Optional[bytearray] = None
    cors_origin: Optional[bytes] = None

    def as_bytearray(
        self, request_line_1: bytearray, url_context: bytearray, request_line_2: bytearray, host_header: bytearray
    ) -> bytearray:
        if url_context:
            if self.url_path:
                self.last_queried_bytes = (
                        request_line_1 + b'/' + url_context + b'/' + self.url_path + request_line_2 + self.headers + host_header + self.content
                )
            else:
                self.last_queried_bytes = (
                        request_line_1 + b'/' + url_context + request_line_2 + self.headers + host_header + self.content
                )
        else:
            if self.url_path:
                self.last_queried_bytes = (
                        request_line_1 + b'/' + self.url_path + request_line_2 + self.headers + host_header + self.content
                )
            else:
                self.last_queried_bytes = (
                        request_line_1 + b'/' + request_line_2 + self.headers + host_header + self.content
                )
        return self.last_queried_bytes
