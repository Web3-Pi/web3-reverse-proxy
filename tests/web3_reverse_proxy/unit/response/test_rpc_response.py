from unittest import TestCase
from unittest.mock import Mock

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class RPCResponseTests(TestCase):
    def setUp(self):
        self.responses = {
            "normal_response": {
                "raw": b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"}\n',
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:41:40 GMT",
                    "content-length": "38",
                },
                "content": {"jsonrpc": "2.0", "id": 0, "result": "1"},
            },
            "compressed_response": {
                "raw": b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00",
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "content-encoding": "gzip",
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:45:33 GMT",
                    "content-length": "62",
                },
                "content": b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00",
            },
            "chunked_response": {
                "raw": b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"Hel\r\nC\r\nlo":"World"}\r\n',
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "transfer-encoding": "chunked",
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:45:33 GMT",
                },
                "content": '5\r\n{"Hel\r\nC\r\nlo":"World"}\r\n',
            },
            "chunked_response_full": {
                "raw": b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"Hel\r\nC\r\nlo":"World"}\r\n0\r\n\r\n',
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "transfer-encoding": "chunked",
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:45:33 GMT",
                },
                "content": '5\r\n{"Hel\r\nC\r\nlo":"World"}\r\n0\r\n\r\n',
            },
            "chunked_response_header_only": {
                "raw": b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n",
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "transfer-encoding": "chunked",
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:45:33 GMT",
                },
                "content": "",
            },
            "chunked_response_shorter_header_only": {
                "raw": b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n",
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "transfer-encoding": "chunked",
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:45:33 GMT",
                },
                "content": "",
            },
            "chunked_response_chunk": {
                "raw": b'C\r\nlo":"World"}\r\n',
                "status_code": None,
                "status": None,
                "protocol": None,
                "headers": None,
                "content": "",
            },
            "http_error_response": {
                "raw": b"HTTP/1.1 500 Internal Server Error\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\n",
                "status_code": 500,
                "status": "Internal Server Error",
                "protocol": "HTTP/1.1",
                "headers": {
                    "date": "Wed, 03 Apr 2024 22:41:40 GMT",
                },
                "content": "",
            },
            "rpc_error_response": {
                "raw": b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0","id":0,"error":{"code":35000,"message":"An error occurred"}}',
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:41:40 GMT",
                    "content-length": "77",
                },
                "content": {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {"code": 35000, "message": "An error occurred"},
                },
            },
            "wonky_headers_response": {
                "raw": b'HTTP/1.1 200 OK\r\ncontent-type: application/json\r\ndATE:Wed, 03 Apr 2024 22:41:40 GMT\r\ncontent-LENGTH: 38 \r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"}\n',
                "status_code": 200,
                "status": "OK",
                "protocol": "HTTP/1.1",
                "headers": {
                    "content-type": "application/json",
                    "date": "Wed, 03 Apr 2024 22:41:40 GMT",
                    "content-length": "38",
                },
                "content": {"jsonrpc": "2.0", "id": 0, "result": "1"},
            },
        }

        self.request_mock = Mock(RPCRequest)

    def test_create(self):
        for response_data in self.responses.values():
            with self.subTest(response=response_data["raw"]):
                request = self.request_mock()
                response = RPCResponse(response_data["raw"], request)
                self.assertEqual(response.raw, response_data["raw"])
                self.assertEqual(response.request, request)
                self.assertEqual(response.status_code, response_data["status_code"])
                self.assertEqual(response.status, response_data["status"])
                self.assertEqual(response.protocol, response_data["protocol"])
                self.assertEqual(response.headers, response_data["headers"])
                self.assertEqual(response.content, response_data["content"])

    def test_chunked_property(self):
        for response_type, response_data in self.responses.items():
            with self.subTest(response=response_data["raw"]):
                is_response_chunked = response_type.startswith("chunked")
                response = RPCResponse(response_data["raw"], self.request_mock())
                self.assertEqual(response.chunked, is_response_chunked)

    def test_compressed_property(self):
        for response_type, response_data in self.responses.items():
            with self.subTest(response=response_data["raw"]):
                is_response_chunked = response_type.startswith("compressed")
                response = RPCResponse(response_data["raw"], self.request_mock())
                self.assertEqual(response.compressed, is_response_chunked)

    def test_get_headers(self):
        for response_data in self.responses.values():
            with self.subTest(response=response_data["raw"]):
                result = RPCResponse.get_headers(response_data["raw"])
                self.assertEqual(result, response_data["headers"])

    def test_is_complete_raw_response(self):
        dataset = [
            (self.responses["normal_response"]["raw"], True),
            (self.responses["compressed_response"]["raw"], True),
            (self.responses["chunked_response_full"]["raw"], True),
            (self.responses["http_error_response"]["raw"], True),
            (self.responses["rpc_error_response"]["raw"], True),
            (self.responses["chunked_response_header_only"]["raw"], False),
            (self.responses["chunked_response_shorter_header_only"]["raw"], False),
            (self.responses["chunked_response_chunk"]["raw"], False),
            (
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{",
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"He',
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"Hel',
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"Hel\r',
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n{"Hel\r\n',
                False,
            ),
            (b"5\r\n{", False),
            (b'5\r\n{"He', False),
            (b'5\r\n{"Hel', False),
            (b'5\r\n{"Hel\r', False),
            (b'5\r\n{"Hel\r\n', False),
            (b"0\r\n\r\n", True),
            (
                b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"}',
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"',
                False,
            ),
            (
                b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0",',
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&",
                False,
            ),
            (
                b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xba",
                False,
            ),
        ]
        for raw_response, is_complete in dataset:
            with self.subTest(response=raw_response):
                result = RPCResponse.is_complete_raw_response(raw_response)
                self.assertEqual(result, is_complete)
