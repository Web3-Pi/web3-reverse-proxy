from dataclasses import dataclass

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest


# FIXME: this class requires implementation from scratch
@dataclass
class RPCResponse:

    # FIXME: parse response headers to correctly receive the whole response
    END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER = b'\x00\x00'
    END_OF_CHUNKED_TRANSMISSION = b'0\r\n\r\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER = b'}\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR = b'}}'

    data: bytearray
    request: RPCRequest

    @classmethod
    # FIXME: parse response headers to correctly receive the whole response
    def hack_is_complete_raw_response(cls, _bytes: bytearray) -> bool:
        return _bytes.endswith(cls.END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER) or \
            _bytes.endswith(cls.END_OF_CHUNKED_TRANSMISSION) or \
            _bytes.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER) or \
            _bytes.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR)
