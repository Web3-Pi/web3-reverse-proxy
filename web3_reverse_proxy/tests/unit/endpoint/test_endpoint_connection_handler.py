from unittest import TestCase
from unittest.mock import Mock

from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpoint_connection_handler import EndpointConnectionHandler


class EndpointConnectionHandlerTests(TestCase):
    def setUp(self):
        self.request_sender_mock = Mock(RequestSender)
        self.response_receiver_mock = Mock(ResponseReceiver)
        self.connection_mock = Mock(
            EndpointConnection,
            req_sender=self.request_sender_mock,
            res_receiver=self.response_receiver_mock
        )
        self.connection_pool_mock = Mock(ConnectionPool)
        self.endpoint_connection_handler = EndpointConnectionHandler(self.connection_mock, self.connection_pool_mock)

    def test_get_receiver_should_return_receiver(self):
        self.assertIs(self.endpoint_connection_handler.get_receiver(), self.response_receiver_mock)

    def test_get_sender_should_return_sender(self):
        self.assertIs(self.endpoint_connection_handler.get_sender(), self.request_sender_mock)

    def test_reconnect_should_reconnect_connection(self):
        self.endpoint_connection_handler.reconnect()
        self.connection_mock.reconnect.assert_called()

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

    def test_reconnect_should_fail_after_release(self):
        self.endpoint_connection_handler.release()
        with self.assertRaises(EndpointConnectionHandler.ConnectionReleasedError):
            self.endpoint_connection_handler.reconnect()

    def test_get_sender_should_fail_after_release(self):
        self.endpoint_connection_handler.release()
        with self.assertRaises(EndpointConnectionHandler.ConnectionReleasedError):
            self.endpoint_connection_handler.reconnect()

    def test_get_receiver_should_fail_after_release(self):
        self.endpoint_connection_handler.release()
        with self.assertRaises(EndpointConnectionHandler.ConnectionReleasedError):
            self.endpoint_connection_handler.reconnect()

    def test_should_release_connection_on_destructor(self):
        del self.endpoint_connection_handler
        self.connection_pool_mock.put.assert_called_once_with(self.connection_mock)
