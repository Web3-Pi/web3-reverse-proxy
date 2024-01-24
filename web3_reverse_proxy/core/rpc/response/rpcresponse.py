from dataclasses import dataclass


# FIXME: this class requires implementation from scratch
@dataclass
class RPCResponse:

    # FIXME: parse response headers to correctly receive the whole response
    END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER = b'\x00\x00'
    END_OF_CHUNKED_TRANSMISSION = b'0\r\n\r\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER = b'}\n'
    END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR = b'}}'
    END_OF_PABLITO_HACK = b'token\n'

    data: bytearray

    @classmethod
    # FIXME: parse response headers to correctly receive the whole response
    def hack_is_complete_raw_response(cls, _bytes: bytearray) -> bool:
        return _bytes.endswith(cls.END_OF_GZIP_TRANSMISSION_WITH_LEN_HEADER) or \
            _bytes.endswith(cls.END_OF_CHUNKED_TRANSMISSION) or \
            _bytes.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER) or \
            _bytes.endswith(cls.END_OF_REGULAR_TRANSMISSION_WITH_LEN_HEADER_ERROR) or \
            _bytes.endswith(cls.END_OF_PABLITO_HACK)
