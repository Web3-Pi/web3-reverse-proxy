import time
from queue import Queue

from web3_reverse_proxy.config.conf import Config
from web3_reverse_proxy.core.inbound.server import InboundServer
from web3_reverse_proxy.core.rpc.request.middleware.defaultmiddlewares.requestreader import (
    RequestReader,
)
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse
from web3_reverse_proxy.core.sockets.clientsocket import ClientSocket

DEFAULT_INSTRUCTIONS = [
    # ("DEFAULT", {"count": 10}),
    # ("DOWN", {"timeout": 10}),
    # ("DEFAULT", {"count": 5}),
    # ("FREEZE", {"timeout": 10}),
]

DEFAULT_RPC_RESPONSE = b'{"jsonrpc":"2.0","id":0,"result":"THIS IS A MOCKED ENDPOINT"}'


DEFAULT_PORT = 8545


class MockEndpoint:
    def __init__(self, port=DEFAULT_PORT, instructions=DEFAULT_INSTRUCTIONS):
        self.port = port
        self.request_reader = RequestReader()
        self.clear_state()
        self.request_counter = 0

        self.instructions = Queue()
        self.current_instruction = None
        self.is_executing_instruction = lambda: False
        for instruction in instructions:
            self.instructions.put_nowait(instruction)

        self.start_server()

    def start_server(self) -> InboundServer:
        print(f"Starting server")
        self.inbound_srv = InboundServer(self.port, Config.BLOCKING_ACCEPT_TIMEOUT)
        print(f"Server listening at port {self.port}")

    def stop_server(self) -> InboundServer:
        print("Shutting down server")
        self.inbound_srv.shutdown()

    def clear_state(self) -> None:
        self.active_sockets = []
        self.sockets_to_close = []

    def fetch_instruction(self):
        if not self.instructions.empty() and not self.is_executing_instruction():
            name, args = self.instructions.get_nowait()
            self.current_instruction = {"name": name, "args": args}
            if args.get("count"):
                self.request_counter = 0
                self.is_executing_instruction = (
                    lambda: self.request_counter < args["count"]
                )
            else:
                self.is_executing_instruction = lambda: False

    @staticmethod
    def get_http_response(payload: bytes) -> bytearray:
        content_length = str(len(payload)).encode()
        return bytearray(
            b"HTTP/1.1 200\r\nContent-Type: application/json\r\nContent-Length: "
            + content_length
            + b"\r\n\r\n"
            + payload
        )

    def get_instruction_name(self) -> str | None:
        return (
            self.current_instruction["name"]
            if self.current_instruction is not None
            else None
        )

    def execute_server_down_instruction(self):
        if self.get_instruction_name() == "DOWN":
            self.stop_server()
            time.sleep(self.current_instruction["args"]["timeout"])
            self.start_server()
            self.current_instruction = None

    def execute_server_freeze_instruction(self):
        if self.get_instruction_name() == "FREEZE":
            print("Freezing")
            time.sleep(self.current_instruction["args"]["timeout"])
            print("Resumed")
            self.current_instruction = None

    def main_loop(self) -> None:
        self.fetch_instruction()

        self.execute_server_down_instruction()

        # Handle incoming connections
        self.inbound_srv.accept_incoming_connections()
        ready_read_connections = self.inbound_srv.remove_ready_read_connections()

        # Handle incoming requests
        for cs in ready_read_connections:
            self.fetch_instruction()
            self.request_response_roundtrip(cs)

        # Update inbound server state
        self.inbound_srv.close_connections(self.sockets_to_close)
        self.inbound_srv.add_active_connections(self.active_sockets)

        self.clear_state()

    def request_response_roundtrip(self, cs: ClientSocket) -> None:
        req, err = self.read_request(cs)
        if err is not None:
            self.handle_errors(cs, err)
            self.sockets_to_close.append(cs)
        else:
            res = self.process_request(req)
            self.handle_response(cs, res)

    def read_request(self, cs: ClientSocket) -> None:
        req, err = self.request_reader.read_request(cs, RPCRequest())

        if req is not None:
            self.request_counter += 1
        return req, err

    def process_request(self, req: RPCRequest) -> None:
        self.execute_server_freeze_instruction()
        return self.get_http_response(DEFAULT_RPC_RESPONSE)

    def send_response(self, cs: ClientSocket, response: bytearray) -> None:
        assert cs.is_ready_write()
        try:
            cs.send_all(response)
            return True
        except:
            return False

    def handle_response(self, cs: ClientSocket, res: bytearray) -> None:
        if self.send_response(cs, res):
            self.active_sockets.append(cs)
        else:
            self.sockets_to_close.append(cs)

    def handle_errors(self, cs: ClientSocket, err: RPCResponse) -> ClientSocket:
        try:
            if cs.is_ready_write():
                cs.send_all(err.raw)
        except:
            pass

    def cleanup(self) -> None:
        self.inbound_srv.shutdown()

    def run_forever(self) -> None:
        try:
            while True:
                self.main_loop()
        except KeyboardInterrupt:
            print("\nTerminating")
            self.cleanup()
        except Exception:
            raise
