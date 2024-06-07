from unittest import TestCase
from unittest.mock import Mock, patch

from web3_reverse_proxy.core.interfaces.rpcnode import LoadBalancer
from web3_reverse_proxy.core.rpc.node.endpoint_connection_pool import (
    EndpointConnectionPool,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import (
    EndpointConnection,
)
from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.interfaces.servicestate import StateUpdater


class EndpointConnectionPoolTests(TestCase):
    def setUp(self):
        self.load_balancer_mock = Mock(LoadBalancer)
        self.load_balancer_mock.get_queue_for_request.return_value = 0
        self.state_updater_mock = Mock(StateUpdater)
        self.connection_desc_mock = Mock(EndpointConnectionDescriptor)

    def configure_endpoint_mock(self, rpc_endpoint_mock):
        endpoint_instance_mock = Mock(RPCEndpoint)
        rpc_endpoint_mock.create.return_value = endpoint_instance_mock

    def create_pool(self, descriptors=None, max_connections=1):
        with patch(
            "web3_reverse_proxy.core.rpc.node.endpoint_connection_pool.RPCEndpoint"
        ) as rpc_endpoint_mock:
            self.configure_endpoint_mock(rpc_endpoint_mock)
            connection_pool = EndpointConnectionPool(
                descriptors or [("endpoint-0", self.connection_desc_mock)],
                self.load_balancer_mock,
            )
            connection_pool.MAX_CONNECTIONS = max_connections
            return connection_pool

    def test_should_create_multiple_endpoints_based_on_descriptors(self):
        descriptors = [
            ("endpoint-0", self.connection_desc_mock),
            ("endpoint-1", self.connection_desc_mock),
        ]
        connection_pool = self.create_pool(descriptors)
        self.assertEqual(len(connection_pool.endpoints), len(descriptors))

    def test_put_should_add_connection_to_pool(self):
        connection_pool = self.create_pool()
        pool_size_before = connection_pool.connections.qsize()

        connection_pool.put(Mock(EndpointConnection))

        self.assertEqual(connection_pool.connections.qsize(), pool_size_before + 1)

    @patch(
        "web3_reverse_proxy.core.rpc.node.endpoint_connection_pool.EndpointConnectionHandler"
    )
    def test_get_should_take_connection_from_pool_if_exists(
        self, connection_handler_mock
    ):
        connection_pool = self.create_pool()
        connection = Mock(EndpointConnection)
        connection_pool.connections.put(connection)
        pool_size_before = connection_pool.connections.qsize()

        connection_pool.get()

        connection_handler_mock.assert_called_with(connection, connection_pool, False)
        self.assertEqual(connection_pool.connections.qsize(), pool_size_before - 1)

    @patch(
        "web3_reverse_proxy.core.rpc.node.endpoint_connection_pool.EndpointConnection"
    )
    @patch(
        "web3_reverse_proxy.core.rpc.node.endpoint_connection_pool.EndpointConnectionHandler"
    )
    def test_get_should_create_new_connection_if_pool_is_empty(
        self, connection_handler_mock, connection_mock
    ):
        connection_pool = self.create_pool()
        pool_size_before = connection_pool.connections.qsize()

        connection_pool.get()

        connection_handler_mock.assert_called_with(
            connection_mock(), connection_pool, True
        )
        self.assertEqual(connection_pool.connections.qsize(), pool_size_before)

    def test_pool_should_close_excessive_connections(self):
        connection_pool = self.create_pool()
        connection = Mock(EndpointConnection)
        other_connection = Mock(EndpointConnection)

        connection_pool.put(connection)
        pool_size_before = connection_pool.connections.qsize()
        connection_pool.put(other_connection)

        self.assertEqual(connection_pool.connections.qsize(), pool_size_before)
        connection.close.assert_called()
        self.assertIs(connection_pool.connections.get_nowait(), other_connection)

    def test_close_should_close_all_connections(self):
        connection_pool = self.create_pool(max_connections=2)
        connection = Mock(EndpointConnection)
        other_connection = Mock(EndpointConnection)

        connection_pool.put(connection)
        connection_pool.put(other_connection)
        connection_pool.close()

        connection.close.assert_called()
        other_connection.close.assert_called()
