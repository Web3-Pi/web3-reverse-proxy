import json
from unittest import TestCase
from unittest.mock import Mock, patch

from tests.web3_reverse_proxy.data.json_rpc import RPCCalls
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator import AcceptJSONRPCContentReader
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware


class AcceptJSONRPCContentReaderTests(TestCase):
    @staticmethod
    def _make_request(payload):
        return RPCRequest(content = json.dumps(payload).encode('utf-8'))
    @staticmethod
    def _pass_request(json_reader, request):
        with patch("web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator.Config", JSON_RPC_REQUEST_PARSER_ENABLED=True):
            return json_reader.read_request(Mock(ClientSocket), request)

    def test_valid_requests_should_pass(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_valid_calls():
            with self.subTest(f'{payload["method"]} -> {payload.get("params")}'):
                request = self._make_request(payload)
                result, _ = self._pass_request(json_reader, request)
                self.assertEqual(result, request)

    def test_requests_missing_members_should_fail(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_missing_member_calls():
            with self.subTest(f'{payload.get("method")} -> {payload.get("params")}'):
                _, response = self._pass_request(json_reader, self._make_request(payload))
                self.assertIn(b'200 OK', response.raw)
                self.assertIn(b'Missing member', response.raw)

    def test_requests_with_non_alphanumeric_characters_should_fail(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_non_alphanumeric_input_calls():
            with self.subTest(f'{payload["method"]} -> {payload.get("params")}'):
                _, response = self._pass_request(json_reader, self._make_request(payload))
                self.assertIn(b'200 OK', response.raw)
                self.assertIn(b'Invalid characters', response.raw)

    def test_should_pass_request_to_next_reader_if_available(self):
        next_reader = Mock(RequestReaderMiddleware)
        json_reader = AcceptJSONRPCContentReader(next_reader)
        payload = RPCCalls.create_json_payload("net_version", None)
        self._pass_request(json_reader, self._make_request(payload))
        next_reader.read_request.assert_called()

    def test_request_format_validation(self):
        test_data = [
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": "2.0"}, True],
            [{"method": 256 , "id": 0, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": None , "id": 0, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": [] , "id": 0, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": {} , "id": 0, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": True , "id": 0, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": "1.0"}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": 2}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": None}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": True}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": []}, False],
            [{"method": "net_version" , "id": 0, "params": [], "jsonrpc": {}}, False],
            [{"method": "net_version" , "id": 0, "params": {}, "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": 0, "params": "", "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": 0, "params": None, "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": 0, "params": 256, "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": 0, "params": True, "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": "0", "params": [], "jsonrpc": "2.0"}, True],
            [{"method": "net_version" , "id": "foo", "params": [], "jsonrpc": "2.0"}, True],
            [{"method": "net_version" , "id": None, "params": [], "jsonrpc": "2.0"}, True],
            [{"method": "net_version" , "id": [], "params": [], "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": {}, "params": [], "jsonrpc": "2.0"}, False],
            [{"method": "net_version" , "id": True, "params": [], "jsonrpc": "2.0"}, False],
        ]
        json_reader = AcceptJSONRPCContentReader()

        for payload, is_valid in test_data:
            with self.subTest(payload=payload):
                request = self._make_request(payload)
                result = self._pass_request(json_reader, request)
                if is_valid:
                    self.assertEqual(result[0], request)
                else:
                    self.assertIn(b'200 OK', result[1].raw)
                    self.assertIn(b'Invalid value for member', result[1].raw)

    def test_passes_invalid_requests_when_disabled(self):
        json_reader = AcceptJSONRPCContentReader()
        test_data = [payload for payload in RPCCalls.generate_missing_member_calls() if payload.get("method") is not None] + RPCCalls.generate_non_alphanumeric_input_calls()

        for payload in test_data:
            with self.subTest(payload=payload):
                with patch("web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator.Config", JSON_RPC_REQUEST_PARSER_ENABLED=False):
                    request = self._make_request(payload)
                    result, _ = json_reader.read_request(Mock(ClientSocket), request)
                    self.assertEqual(result, request)

    def test_fails_on_missing_method_when_disabled(self):
        json_reader = AcceptJSONRPCContentReader()
        test_data = [payload for payload in RPCCalls.generate_missing_member_calls() if payload.get("method") is None]

        for payload in test_data:
            with self.subTest(payload=payload):
                with patch("web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator.Config", JSON_RPC_REQUEST_PARSER_ENABLED=False):
                    _, response = json_reader.read_request(Mock(ClientSocket), self._make_request(payload))
                    self.assertIn(b"Missing method field", response.raw)
