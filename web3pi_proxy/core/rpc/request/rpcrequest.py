from dataclasses import dataclass


@dataclass
class RPCRequest:
    user_api_key: str | None = None
    headers: bytearray | None = None
    content_len: int = -1
    content: bytearray | None = None
    method: str = ""
    id: int | str | None = None
    priority: int = 0
    constant_pool: str | None = None
    last_queried_bytes: bytearray | None = None
    keep_alive: bool = True

    def as_bytearray(
        self, request_line: bytearray, host_header: bytearray
    ) -> bytearray:
        self.last_queried_bytes = (
            request_line + self.headers + host_header + self.content
        )
        return self.last_queried_bytes
