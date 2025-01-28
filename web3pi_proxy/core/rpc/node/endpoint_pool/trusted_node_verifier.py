import json
from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import EndpointConnectionDescriptor
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class TrustedNodeVerifier:

    def __init__(self, trusted_node_url: str):
        self.trusted_node_connection_descriptor = EndpointConnectionDescriptor.from_url(trusted_node_url)

    def get_trusted_node_connection_descriptor(self):
        return self.trusted_node_connection_descriptor

    def verify(self, req: RPCRequest, node_response: bytes, trusted_response: bytes) -> bool:
        try:
            node_response_json = json.loads(node_response)
            trusted_response_json = json.loads(trusted_response)

            # Validate the structure of both responses and ensure they are JSON-RPC
            if not self._is_valid_jsonrpc_response(node_response_json) or \
                    not self._is_valid_jsonrpc_response(trusted_response_json):
                self.log_discrepancy(node_response, trusted_response, reason="Invalid JSON-RPC structure")
                return False

            # Strict compare the "result" field
            if node_response_json.get("result") == trusted_response_json.get("result"):
                print("Verified! OK")
                return True
            else:
                self.log_discrepancy(node_response, trusted_response, reason="Result mismatch")
                return False

        except json.JSONDecodeError as e:
            # Handle invalid JSON formats
            self.log_discrepancy(node_response, trusted_response, reason=f"Invalid JSON: {e}")
            return False
        except Exception as e:
            # Handle unexpected exceptions
            self.log_discrepancy(node_response, trusted_response, reason=f"Unexpected error: {e}")
            return False

    def _is_valid_jsonrpc_response(self, response: dict) -> bool:
        return (
                isinstance(response, dict) and
                response.get("jsonrpc") == "2.0" and
                ("result" in response or "error" in response) and
                "id" in response
        )

    def log_discrepancy(self, node_response, trusted_response):
        print("Discrepancy detected!")
        print(f"Main Node Response: {node_response}")
        print(f"Trusted Node Response: {trusted_response}")