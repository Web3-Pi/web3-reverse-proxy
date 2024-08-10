from dataclasses import dataclass


@dataclass
class RPCRequest:
    user_api_key: str | None = None
    url_path: bytearray | None = None
    headers: bytearray | None = None
    content_len: int = -1
    content: bytearray | None = None
    method: str = ""
    id: int | str | None = None
    priority: int = 0
    constant_pool: str | None = None
    last_queried_bytes: bytearray | None = None
    keep_alive: bool = True
    http_method: bytearray | None = None
    cors_origin: bytes | None = None

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
