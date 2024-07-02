from unittest import TestCase
from unittest.mock import Mock

from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.rpc.request.middleware.defaultmiddlewares.requestreader import (
    RequestReader,
)
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.sockets.clientsocket import ClientSocket


class RequestReaderTests(TestCase):
    def setUp(self):
        self.socket_mock = Mock(ClientSocket)
        self.request_reader_mock = Mock(RequestReaderMiddleware)

    def test_parses_request(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"POST /aaa HTTP/1.1\r\n",
            b"Host: localhost:6512\r\n",
            b"User-Agent: curl/8.0.1\r\n",
            b"Accept: */*\r\n",
            b"Content-Type: application/json\r\n",
            b"Content-Length: 59\r\n",
            b"\r\n",
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        ]
        request_reader = RequestReader()
        rpc_request = RPCRequest()

        result_request, _ = request_reader.read_request(sock, rpc_request)

        self.assertEqual(result_request.content_len, 59)
        self.assertEqual(
            result_request.headers,
            b"User-Agent: curl/8.0.1\r\nAccept: */*\r\nContent-Type: application/json\r\nContent-Length: 59\r\n",
        )
        self.assertEqual(
            result_request.content,
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        )
        self.assertEqual(result_request.content_len, 59)

    def test_handles_wonky_headers(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"POST /aaa HTTP/1.1\r\n",
            b"host: localhost:6512\r\n",
            b"user-AGENT: curl/8.0.1\r\n",
            b"aCCEPT: */*\r\n",
            b"Content-Type: application/json\r\n",
            b"cOnTEnT-LeNgTH: 59\r\n",
            b"\r\n",
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        ]
        request_reader = RequestReader()
        rpc_request = RPCRequest()

        result_request, _ = request_reader.read_request(sock, rpc_request)

        self.assertEqual(result_request.content_len, 59)
        self.assertEqual(
            result_request.headers,
            b"user-AGENT: curl/8.0.1\r\naCCEPT: */*\r\nContent-Type: application/json\r\ncOnTEnT-LeNgTH: 59\r\n",
        )

    def test_empty_body_should_fail(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"POST /aaa HTTP/1.1\r\n",
            b"Host: localhost:6512\r\n",
            b"User-Agent: curl/8.0.1\r\n",
            b"Accept: */*\r\n",
            b"Content-Type: application/json\r\n",
            b"Content-Length: 0\r\n",
            b"\r\n",
        ]
        request_reader = RequestReader()
        rpc_request = RPCRequest()

        _, response = request_reader.read_request(sock, rpc_request)

        self.assertIn(b"400", response.raw)
        self.assertIn(b"Bad Request", response.raw)

    def test_wrong_method_should_fail(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"GET /aaa HTTP/1.1\r\n",
            b"Host: localhost:6512\r\n",
            b"User-Agent: curl/8.0.1\r\n",
            b"Accept: */*\r\n",
            b"Content-Type: application/json\r\n",
            b"Content-Length: 59\r\n",
            b"\r\n",
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        ]
        request_reader = RequestReader()
        rpc_request = RPCRequest()

        _, response = request_reader.read_request(sock, rpc_request)

        self.assertIn(b"405", response.raw)
        self.assertIn(b"Method Not Allowed", response.raw)

    def test_returns_response_on_bad_request(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"POST /aaa HTTP/1.1\r\n",
            b"hostlocalhost6512\r\n",
            b"User-Agent: curl/8.0.1\r\n",
            b"Accept: */*\r\n",
            b"Content-Type: application/json\r\n",
            b"Content-Length: 59\r\n",
            b"\r\n",
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        ]
        request_reader = RequestReader()
        rpc_request = RPCRequest()

        # import pytest; pytest.set_trace()
        _, response = request_reader.read_request(sock, rpc_request)

        self.assertIn(b"400", response.raw)
        self.assertIn(b"Bad Request", response.raw)
