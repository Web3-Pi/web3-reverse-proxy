from unittest import TestCase
from unittest.mock import Mock, call

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.receiver import (
    ResponseReceiverGeth,
)
from web3pi_proxy.core.sockets.basesocket import BaseSocket


class ResponseReceiverGethTests(TestCase):
    def setUp(self):
        self.socket_mock = Mock(BaseSocket)

    def test_receive_chunked_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n",
            b'{"Hel\r\nA\r\nlo":',
            b'"World\r\n2\r',
            b'\n"}\r\n',
            b"0\r\n\r\n",
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        expected_callback_calls = [
            call(
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n"
            ),
            call(b'{"Hel\r\nA\r\nlo":'),
            call(b'"World\r\n2\r'),
            call(b'\n"}\r\n'),
            call(b"0\r\n\r\n"),
        ]

        receiver.recv_response(callback)
        callback.assert_has_calls(expected_callback_calls)

    def test_receive_regular_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id"',
            b':0,"result":"1"}\n',
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        receiver.recv_response(callback)

        callback.assert_has_calls(
            [
                call(
                    b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id"'
                ),
                call(b':0,"result":"1"}\n'),
            ]
        )

    def test_receive_compressed_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00",
            b"\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00",
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        receiver.recv_response(callback)

        callback.assert_has_calls(
            [
                call(
                    b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00"
                ),
                call(
                    b"\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00"
                ),
            ]
        )

    def test_receive_rpc_error_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0",',
            b'"id":0,"error":{"code":35000,"message":"An error occurred"}}',
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        receiver.recv_response(callback)

        callback.assert_has_calls(
            [
                call(
                    b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0",'
                ),
                call(b'"id":0,"error":{"code":35000,"message":"An error occurred"}}'),
            ]
        )
