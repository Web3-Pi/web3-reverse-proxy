from dataclasses import dataclass


@dataclass
class RPCRequest:
    user_api_key: str = ""
    headers: bytearray | None = None
    content_len: int = -1
    content: bytearray | None = None
    method: str = ""
    id: int | str | None = None
    priority: int = 0
    last_queried_bytes: bytearray | None = None

    def as_bytearray(self, request_line: bytearray, host_header: bytearray) -> bytearray:
        self.last_queried_bytes = request_line + self.headers + host_header + self.content
        return self.last_queried_bytes
