import json
from typing import Any, Dict, Optional, Tuple

from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


# FIXME: this class requires implementation from scratch
class RPCResponse:
    # FIXME: parse response headers to correctly receive the whole response
    START_OF_TRANSMISSION = b"HTTP"
    END_OF_CHUNKED_TRANSMISSION = b"0\r\n\r\n"

    HEAD_SEPARATOR = b"\r\n\r\n"
    CRLF_SEPARATOR = b"\r\n"
    RAW_ENCODING = "utf-8"

    raw: bytearray
    request: RPCRequest
    status_code: Optional[int] = None
    status: Optional[str] = None
    protocol: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    content: Any = ""

    def __init__(self, data: bytearray, request: RPCRequest):
        self.raw = data
        self.request = request
        if data.startswith(self.START_OF_TRANSMISSION):
            self._parse_response(data)

    @property
    def chunked(self) -> bool:
        return self._is_chunked(self.headers)

    @property
    def compressed(self) -> bool:
        return self._is_compressed(self.headers)

    @property
    def is_complete(self) -> bool:
        return type(self.content) is dict or self._verify_completion(
            self.content, self.headers
        )

    @staticmethod
    def _is_compressed(headers: Dict[str, str]) -> bool:
        return headers is not None and "gzip" in headers.get("content-encoding", "")

    @staticmethod
    def _is_chunked(headers: Dict[str, str]) -> bool:
        return headers is None or "chunked" in headers.get("transfer-encoding", "")

    @classmethod
    def _separate_head_from_body(
        cls, raw_data: bytearray
    ) -> Tuple[Optional[bytearray], bytearray]:
        if not raw_data.startswith(cls.START_OF_TRANSMISSION):
            return None, raw_data
        head, _, body = raw_data.partition(cls.HEAD_SEPARATOR)
        return head, body

    @classmethod
    def _parse_headers(cls, headers_data: bytearray) -> Dict[str, str]:
        raw_headers_list = headers_data.split(cls.CRLF_SEPARATOR)
        if raw_headers_list[-1] == b"":
            raw_headers_list.pop(-1)

        headers = {}
        for raw_header in raw_headers_list:
            name, _, value = raw_header.decode(cls.RAW_ENCODING).partition(":")
            headers[name.lower()] = value.strip()
        return headers

    @classmethod
    def get_headers(cls, raw_data: bytearray) -> Optional[Dict[str, str]]:
        head, _ = cls._separate_head_from_body(raw_data)
        if head is None:
            return None
        return cls._parse_headers(head.partition(cls.CRLF_SEPARATOR)[2])

    @classmethod
    def is_complete_raw_response(cls, raw_data: bytearray) -> bool:
        head, body = cls._separate_head_from_body(raw_data)
        headers = (
            cls._parse_headers(head.partition(cls.CRLF_SEPARATOR)[2])
            if head is not None
            else None
        )
        return cls._verify_completion(body, headers)

    @classmethod
    def _verify_completion(
        cls, body: bytearray, headers: Optional[Dict[str, str]]
    ) -> bool:
        if cls._is_chunked(headers):
            return body.endswith(cls.END_OF_CHUNKED_TRANSMISSION)
        assert headers is not None
        content_length = headers.get("content-length", 0)
        return len(body) == int(content_length)

    def _process_content(self, body: bytearray) -> None:
        if self.compressed:
            self.content = body
        else:
            self.content = body.decode(self.RAW_ENCODING)
            if (
                len(self.content) > 0
                and not self.chunked
                and not self.headers.get("content-type", "").lower() == "text/plain"
                and self._verify_completion(body, self.headers)
            ):
                self.content = json.loads(self.content)

    def _parse_response(self, raw_data: bytearray) -> None:
        assert raw_data is not None
        head, body = self._separate_head_from_body(raw_data)
        status_line, _, headers = head.partition(self.CRLF_SEPARATOR)
        protocol, _, status = status_line.partition(b" ")
        self.status_code = int(status[:3])
        self.status = status[4:].decode(self.RAW_ENCODING)
        self.protocol = protocol.decode(self.RAW_ENCODING)
        self.headers = self._parse_headers(headers)
        self._process_content(body)

    def append(self, raw_content: bytearray):
        self.raw += raw_content
        _, body = self._separate_head_from_body(self.raw)
        self._process_content(body)
