from web3_reverse_proxy.core.rpc.node.connection_pool import ConnectionPool
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.connection_handler import ConnectionHandler
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnection import EndpointConnection
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.sender import RequestSender
from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.receiver import ResponseReceiver


class EndpointConnectionHandler(ConnectionHandler):
    def __init__(
            self,
            connection: EndpointConnection,
            connection_pool: ConnectionPool
        ) -> None:
        self.connection = connection
        self.connection_pool = connection_pool

    def get_sender(self) -> RequestSender:
        return self.connection.req_sender

    def get_receiver(self) -> ResponseReceiver:
        return self.connection.res_receiver

    def release(self) -> None:
        self.connection_pool.put(self.connection)
