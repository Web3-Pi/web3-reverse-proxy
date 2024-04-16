from dataclasses import dataclass

from httptools import HttpRequestParser

no_messages = 0


class ParserProto:

    def on_message_begin(self):
        pass
        # print("On Mesg Begin")

    def on_url(self, url: bytes):
        print(f"On URL {url}")

    def on_header(self, name: bytes, value: bytes):
        pass
        # print(f"On Header {name}: {value}")

    def on_headers_complete(self):
        pass
        # print(f"On Headers complete")

    def on_body(self, body: bytes):
        pass
        # print(f"On Body {body}")

    def on_message_complete(self):
        global no_messages

        no_messages += 1

        if no_messages % 500 == 0:
            print()
            print(f"Intermediary parsed {no_messages} messages")
            print()

        pass
        # print(f"On Message Complete")

    def on_chunk_header(self):
        pass
        # print(f"On Chunk Header")

    def on_chunk_complete(self):
        pass
        # print(f"On Chunk Complete")

    def on_status(self, status: bytes):
        pass
        # print(f"On Status {status}")


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
    proto: ParserProto = ParserProto()
    parser: HttpRequestParser = HttpRequestParser(proto)

    def append_raw_data(self, data: bytes) -> None:
        pass
        # self.parser.feed_data(data)
        # print(self.parser.get_method())

    def as_bytearray(self, request_line: bytearray, host_header: bytearray) -> bytearray:
        self.last_queried_bytes = request_line + self.headers + host_header + self.content
        return self.last_queried_bytes
