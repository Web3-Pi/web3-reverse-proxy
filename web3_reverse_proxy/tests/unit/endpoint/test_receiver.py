from unittest import TestCase
from unittest.mock import Mock, call

from web3_reverse_proxy.core.sockets.basesocket import BaseSocket
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiverGeth, ResponseReceiverSSL


class ResponseReceiverGethTests(TestCase):
    def setUp(self):
        self.socket_mock = Mock(BaseSocket)

    def test_receive_chunked_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n5\r\n',
            b'{"Hel\r\nA\r\nlo":',
            b'"World\r\n2\r',
            b'\n"}\r\n',
            b'0\r\n\r\n',
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        expected_callback_calls = [
            call(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n'),
            call(b'5\r\n{"Hel\r\n'),
            call(b'A\r\nlo":"World\r\n'),
            call(b'2\r\n"}\r\n'),
            call(b'0\r\n\r\n'),
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

        callback.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"}\n')

    def test_receive_compressed_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00',
            b'\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00',
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        receiver.recv_response(callback)

        callback.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00')

    def test_receive_rpc_error_response(self):
        sock = self.socket_mock()
        sock.recv.side_effect = [
            b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0",',
            b'"id":0,"error":{"code":35000,"message":"An error occurred"}}',
        ]
        receiver = ResponseReceiverGeth(sock)
        callback = Mock()

        receiver.recv_response(callback)

        callback.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0","id":0,"error":{"code":35000,"message":"An error occurred"}}')


class ResponseReceiverSSLTests(TestCase):
    def setUp(self):
        self.socket_mock = Mock(BaseSocket)
        self.rfile_mock = Mock()

    def get_socket(self):
        sock = self.socket_mock()
        sock.socket.makefile.return_value = self.rfile_mock
        return sock

    def test_receive_chunked_response(self):
        self.rfile_mock.readline.side_effect = [
            b'HTTP/1.1 200 OK\r\n',
            b'Transfer-Encoding: chunked\r\n',
            b'Content-Type: application/json\r\n',
            b'Date: Wed, 03 Apr 2024 22:45:33 GMT\r\n',
            b'\r\n',
            b'5\r\n',
            b'A\r\n',
            b'2\r\n',
            b'0\r\n',
        ]
        self.rfile_mock.read.side_effect = [
            b'{"Hel\r\n',
            b'lo":"World\r\n',
            b'"}\r\n',
            b'\r\n',
        ]
        receiver = ResponseReceiverSSL(self.get_socket())
        callback_mock = Mock()

        expected_read_calls = [
            call(7),
            call(12),
            call(4),
            call(2)
        ]
        expected_callback_calls = [
            call(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\n\r\n'),
            call(b'5\r\n{"Hel\r\n'),
            call(b'A\r\nlo":"World\r\n'),
            call(b'2\r\n"}\r\n'),
            call(b'0\r\n\r\n'),
        ]

        receiver.recv_response(callback_mock)

        self.rfile_mock.readline.assert_called()
        self.rfile_mock.read.assert_has_calls(expected_read_calls)
        callback_mock.assert_has_calls(expected_callback_calls)

    def test_receive_regular_response(self):
        self.rfile_mock.readline.side_effect = [
            b'HTTP/1.1 200 OK\r\n',
            b'Content-Type: application/json\r\n',
            b'Date: Wed, 03 Apr 2024 22:41:40 GMT\r\n',
            b'Content-Length: 38\r\n',
            b'\r\n',
        ]
        self.rfile_mock.read.side_effect = [b'{"jsonrpc":"2.0","id":0,"result":"1"}\n']
        receiver = ResponseReceiverSSL(self.get_socket())
        callback_mock = Mock()

        receiver.recv_response(callback_mock)

        self.rfile_mock.readline.assert_called()
        self.rfile_mock.read.assert_called_once_with(38)
        callback_mock.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 38\r\n\r\n{"jsonrpc":"2.0","id":0,"result":"1"}\n')

    def test_receive_compressed_response(self):
        self.rfile_mock.readline.side_effect = [
            b'HTTP/1.1 200 OK\r\n',
            b'Content-Encoding: gzip\r\n',
            b'Content-Type: application/json\r\n',
            b'Date: Wed, 03 Apr 2024 22:45:33 GMT\r\n',
            b'Content-Length: 62\r\n',
            b'\r\n',
        ]
        self.rfile_mock.read.side_effect = [b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00']
        receiver = ResponseReceiverSSL(self.get_socket())
        callback_mock = Mock()

        receiver.recv_response(callback_mock)

        self.rfile_mock.readline.assert_called()
        self.rfile_mock.read.assert_called_once_with(62)
        callback_mock.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:45:33 GMT\r\nContent-Length: 62\r\n\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xaaV\xca*\xce\xcf+*HV\xb2R2\xd23P\xd2Q\xcaLQ\xb22\xd0Q*J-.\xcd)Q\xb2R2T\xaa\xe5\x02\x04\x00\x00\xff\xff\xbaeLj&\x00\x00\x00')

    def test_receive_rpc_error_response(self):
        self.rfile_mock.readline.side_effect = [
            b'HTTP/1.1 200 OK\r\n',
            b'Content-Type: application/json\r\n',
            b'Date: Wed, 03 Apr 2024 22:41:40 GMT\r\n',
            b'Content-Length: 77\r\n',
            b'\r\n',
        ]
        self.rfile_mock.read.side_effect = [b'{"jsonrpc":"2.0","id":0,"error":{"code":35000,"message":"An error occurred"}}']
        receiver = ResponseReceiverSSL(self.get_socket())
        callback_mock = Mock()

        receiver.recv_response(callback_mock)

        self.rfile_mock.readline.assert_called()
        self.rfile_mock.read.assert_called_once_with(77)
        callback_mock.assert_called_once_with(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nDate: Wed, 03 Apr 2024 22:41:40 GMT\r\nContent-Length: 77\r\n\r\n{"jsonrpc":"2.0","id":0,"error":{"code":35000,"message":"An error occurred"}}')
