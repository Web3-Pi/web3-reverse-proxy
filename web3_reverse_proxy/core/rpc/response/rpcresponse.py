from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest

import json
from typing import Any, Dict


# FIXME: this class requires implementation from scratch
class RPCResponse:
    # FIXME: parse response headers to correctly receive the whole response
    START_OF_TRANSMISSION = b'HTTP'
    END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER = b'\x00\x00'
    END_OF_CHUNKED_TRANSMISSION = b'0\r\n\r\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER = b'}\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR = b'}}'

    HEAD_SEPARATOR = b"\r\n\r\n"
    CRLF_SEPARATOR = b"\r\n"
    RAW_ENCODING = "utf-8"

    raw: bytearray
    request: RPCRequest
    status_code: int | None = None
    status: str | None = None
    protocol: str | None = None
    headers: Dict[str, str] | None = None
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

    @staticmethod
    def _is_compressed(headers: Dict[str, str]) -> bool:
        return headers is not None and headers.get("Content-Encoding") == "gzip"

    @staticmethod
    def _is_chunked(headers: Dict[str, str]) -> bool:
        return headers is None or headers.get("Transfer-Encoding") == "chunked"

    @classmethod
    def _parse_headers(cls, headers_data: bytearray) -> Dict[str, str]:
        raw_headers_list = headers_data.split(cls.CRLF_SEPARATOR)
        if raw_headers_list[-1] == b"":
            raw_headers_list.pop(-1)

        headers = {}
        for raw_header in raw_headers_list:
            name, value = raw_header.decode(cls.RAW_ENCODING).split(": ")
            headers[name] = value
        return headers

    @classmethod
    def is_chunked(self, raw_response: bytearray) -> bool:
        return self._is_chunked(self.get_headers(raw_response))

    @classmethod
    def get_headers(cls, raw_data: bytearray) -> Dict[str, str]:
        if not raw_data.startswith(cls.START_OF_TRANSMISSION):
            return None
        head, _, _ = raw_data.partition(cls.HEAD_SEPARATOR)
        return cls._parse_headers(head.partition(cls.CRLF_SEPARATOR)[2])

    @classmethod
    def _verify_completion(cls, raw_data: bytearray, headers: Dict[str, str]) -> bool:
        if cls._is_chunked(headers):
            return raw_data.endswith(cls.END_OF_CHUNKED_TRANSMISSION)
        # TODO: Gzip might require content length check
        if cls._is_compressed(headers):
            return raw_data.endswith(cls.END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER)
        return raw_data.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER) or \
            raw_data.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR)

    def _parse_response(self, raw_data: bytearray) -> None:
        head, _, body = raw_data.partition(self.HEAD_SEPARATOR)
        status_line, _, headers = head.partition(self.CRLF_SEPARATOR)
        protocol, _, status = status_line.partition(b" ")
        self.status_code = int(status[:3])
        self.status = status[4:].decode(self.RAW_ENCODING)
        self.protocol = protocol.decode(self.RAW_ENCODING)
        self.headers = self._parse_headers(headers)
        if self.compressed:
            self.content = body
        else:
            self.content = body.decode(self.RAW_ENCODING)
            if not self.chunked and self._verify_completion(raw_data, self.headers):
                self.content = json.loads(self.content)

    @classmethod
    def is_complete_raw_response(cls, raw_data: bytearray) -> bool:
        headers = cls.get_headers(raw_data)
        return cls._verify_completion(raw_data, headers)

