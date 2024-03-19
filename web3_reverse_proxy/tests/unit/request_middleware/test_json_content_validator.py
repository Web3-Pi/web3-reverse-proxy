import json
from unittest import TestCase
from unittest.mock import Mock

from web3_reverse_proxy.tests.data.json_rpc import RPCCalls
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket
from web3_reverse_proxy.core.rpc.request.middleware.jsonrpcmiddlewares.jsoncontentvalidator import AcceptJSONRPCContentReader
from web3_reverse_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware


class AcceptJSONRPCContentReaderTests(TestCase):
    @staticmethod
    def _pass_request(json_reader, payload):
        request = RPCRequest(content = json.dumps(payload).encode('utf-8'))
        return json_reader.read_request(Mock(ClientSocket), request)

    def test_valid_requests_should_pass(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_valid_calls():
            with self.subTest(f'{payload["method"]} -> {payload.get("params")}'):
                result = self._pass_request(json_reader, payload)
                self.assertIsNone(result)

    def test_requests_missing_members_should_fail(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_missing_member_calls():
            with self.subTest(f'{payload.get("method")} -> {payload.get("params")}'):
                _, response = self._pass_request(json_reader, payload)
                self.assertIn(b'200 OK', response.data)
                self.assertIn(b'Missing member', response.data)

    def test_requests_with_non_alphanumeric_characters_should_fail(self):
        json_reader = AcceptJSONRPCContentReader()

        for payload in RPCCalls.generate_non_alphanumeric_input_calls():
            with self.subTest(f'{payload["method"]} -> {payload.get("params")}'):
                _, response = self._pass_request(json_reader, payload)
                self.assertIn(b'200 OK', response.data)
                self.assertIn(b'Invalid characters', response.data)

    def test_should_pass_request_to_next_reader_if_available(self):
        next_reader = Mock(RequestReaderMiddleware)
        json_reader = AcceptJSONRPCContentReader(next_reader)
        payload = RPCCalls.create_json_payload("net_version", None)
        self._pass_request(json_reader, payload)
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
            with self.subTest(payload):
                result = self._pass_request(json_reader, payload)
                if is_valid:
                    self.assertIsNone(result)
                else:
                    self.assertIn(b'200 OK', result[1].data)
                    self.assertIn(b'Invalid value for member', result[1].data)
