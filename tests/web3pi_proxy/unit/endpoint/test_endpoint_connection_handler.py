from unittest import TestCase
from unittest.mock import DEFAULT, Mock

import pytest

from web3pi_proxy.core.rpc.node.endpoint_pool.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import (
    BrokenConnectionError,
    BrokenFreshConnectionError,
    ConnectionReleasedError,
    EndpointConnectionHandler,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import (
    EndpointConnection,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.receiver import (
    ResponseReceiver,
)
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class EndpointConnectionHandlerTests(TestCase):
    def setUp(self):
        self.sent_request_mock = bytearray(b"sent_request")
        self.request_sender_mock = Mock(RequestSender)
        self.request_sender_mock.send_request.return_value = self.sent_request_mock
        self.response_mock = bytearray(b"response")
        self.response_receiver_mock = Mock(ResponseReceiver)
        self.response_receiver_mock.recv_response.return_value = self.response_mock
        self.connection_mock = Mock(
            EndpointConnection,
            req_sender=self.request_sender_mock,
            res_receiver=self.response_receiver_mock,
        )
        self.connection_pool_mock = Mock(EndpointConnectionPool)
        self.endpoint_connection_handler = EndpointConnectionHandler(
            self.connection_mock, self.connection_pool_mock
        )

    @pytest.mark.skip("TODO: fixme")
    def test_receive_should_return_receiver(self):
        self.assertIs(
            self.endpoint_connection_handler.receive(Mock()), self.response_mock
        )

    def test_send_should_return_sender(self):
        self.assertIs(
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            ),
            self.sent_request_mock,
        )

    def test_send_should_retry_on_connection_fail(self):
        self.request_sender_mock.send_request.side_effect = [OSError, DEFAULT]
        self.assertIs(
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            ),
            self.sent_request_mock,
        )
        self.connection_mock.reconnect.assert_called_once()

    def test_send_should_raise_on_connection_fail_after_retry(self):
        self.request_sender_mock.send_request.side_effect = [OSError, OSError]
        with self.assertRaises(BrokenConnectionError):
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            ),
        self.connection_mock.reconnect.assert_called_once()

    def test_send_should_raise_on_fresh_connection_fail(self):
        self.endpoint_connection_handler.is_reconnect_forbidden = True
        self.request_sender_mock.send_request.side_effect = [OSError]
        with self.assertRaises(BrokenFreshConnectionError):
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            )
        self.connection_mock.reconnect.assert_not_called()

    def test_send_should_raise_if_connection_fails_after_first_send(self):
        self.request_sender_mock.send_request.side_effect = [DEFAULT, OSError]
        self.endpoint_connection_handler.send(
            RPCRequest(
                content=self.sent_request_mock,
                content_len=len(self.sent_request_mock),
            ),
        )

        with self.assertRaises(BrokenFreshConnectionError):
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            )

        self.connection_mock.reconnect.assert_not_called()

    def test_send_should_raise_on_reconnect_fail(self):
        self.request_sender_mock.send_request.side_effect = [OSError]
        self.connection_mock.reconnect.side_effect = [OSError]
        with self.assertRaises(BrokenConnectionError):
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            )

    def test_release_should_put_connection_in_pool(self):
        self.endpoint_connection_handler.release()
        self.connection_pool_mock.put.assert_called_with(self.connection_mock)

    def test_close_should_close_connection(self):
        self.endpoint_connection_handler.close()
        self.connection_mock.close.assert_called()

    def test_close_should_do_nothing_after_release(self):
        self.endpoint_connection_handler.release()
        self.endpoint_connection_handler.close()
        self.connection_mock.close.assert_not_called()

    def test_release_should_do_nothing_after_release(self):
        self.endpoint_connection_handler.release()
        self.endpoint_connection_handler.release()
        self.connection_pool_mock.put.assert_called_once_with(self.connection_mock)

    def test_send_should_fail_after_release(self):
        self.endpoint_connection_handler.release()
        with self.assertRaises(ConnectionReleasedError):
            self.endpoint_connection_handler.send(
                RPCRequest(
                    content=self.sent_request_mock,
                    content_len=len(self.sent_request_mock),
                ),
            ),

    def test_receive_should_fail_after_release(self):
        self.endpoint_connection_handler.release()
        with self.assertRaises(ConnectionReleasedError):
            self.endpoint_connection_handler.receive(Mock())

    def test_should_release_connection_on_destructor(self):
        del self.endpoint_connection_handler
        self.connection_pool_mock.put.assert_called_once_with(self.connection_mock)
