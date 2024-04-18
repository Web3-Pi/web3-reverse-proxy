import json
from unittest import TestCase
from unittest.mock import Mock

from web3_reverse_proxy.tests.data.json_rpc import RPCCalls
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.defaultmiddlewares.headersparser import ParseHeadersRequestReader
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware


class ParseHeadersRequestReaderTests(TestCase):
    def setUp(self):
        self.request_reader_mock = Mock(RequestReaderMiddleware)
        self.socket_mock = Mock(ClientSocket)
        self.rfile_mock = Mock()

    def get_socket(self):
        sock = self.socket_mock()
        sock.get_read_fd.return_value = self.rfile_mock
        return sock

    def test_handles_wonky_headers(self):
        self.rfile_mock.readline.side_effect = [
            b'host: localhost:6512\r\n',
            b'user-AGENT: curl/8.0.1\r\n',
            b'aCCEPT: */*\r\n',
            b'Content-Type: application/json\r\n',
            b'cOnTEnT-LeNgTH: 59\r\n',
            b'\r\n',
            b'{"jsonrpc":"2.0","method":"net_version","params":[],"id":0}',
        ]
        next_reader = self.request_reader_mock()
        next_reader.read_request = lambda _, request: request
        headers_parser = ParseHeadersRequestReader(next_reader)
        socket = self.get_socket()
        rpc_request = RPCRequest(user_api_key="aaa")

        result_request = headers_parser.read_request(socket, rpc_request)

        self.assertEqual(result_request.content_len, 59)
        self.assertEqual(
            result_request.headers,
            b'user-AGENT: curl/8.0.1\r\naCCEPT: */*\r\nContent-Type: application/json\r\ncOnTEnT-LeNgTH: 59\r\n',
        )
