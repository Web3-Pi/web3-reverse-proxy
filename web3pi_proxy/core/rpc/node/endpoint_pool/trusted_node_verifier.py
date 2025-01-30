import gzip
import json

from web3pi_proxy.core.rpc.node.rpcendpoint.connection.connectiondescr import (
    EndpointConnectionDescriptor,
)
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.utils.logger import get_logger


class TrustedNodeVerifier:
    def __init__(self, trusted_node_url: str):
        self.__trusted_node_connection_descriptor = (
            EndpointConnectionDescriptor.from_url(trusted_node_url)
        )
        self.__logger = get_logger("TrustedNodeVerifier")

        self.__comparison_rules = {
            "web3_clientVersion": ["content_length", "body_size"],
            "eth_getLogs": ["content_length", "body_size", "body_content"],
            # TODO: define other rules
        }

    def get_trusted_node_connection_descriptor(self):
        return self.__trusted_node_connection_descriptor

    def verify(
        self, req: RPCRequest, node_response_raw: bytes, trusted_response_raw: bytes
    ) -> bool:
        try:
            self.__logger.debug("Verifying response from trusted node...")

            comparison_types = self.__comparison_rules.get(
                req.method, ["content_length", "body_size"]
            )

            for comparison_type in comparison_types:
                comparison_method_name = f"_compare_{comparison_type}"
                comparison_method = getattr(self, comparison_method_name, None)

                if comparison_method is None:
                    self.__logger.error(
                        f"Comparison method '{comparison_type}' is not implemented."
                    )
                    raise NotImplementedError(
                        f"Comparison method '{comparison_type}' is not implemented."
                    )

                if comparison_method(node_response_raw, trusted_response_raw) is False:
                    return False

            self.__logger.debug("Responses match successfully!")
            return True
        except Exception as e:
            self.__logger.error(f"Error during verification: {e}")
            return False

    def __parse_headers(self, raw_response: bytes) -> dict:
        try:
            headers_raw, _ = raw_response.split(b"\r\n\r\n", 1)
            headers_lines = headers_raw.split(b"\r\n")[1:]

            headers = {}
            for line in headers_lines:
                key, value = line.split(b": ", 1)
                headers[key.decode("utf-8").lower()] = value.decode("utf-8")

            return headers
        except Exception as e:
            self.__logger.error(f"Failed to parse headers: {e}")
            raise

    def __parse_body(self, raw_response: bytes, headers: dict) -> dict:
        try:
            _, body = raw_response.split(b"\r\n\r\n", 1)

            if headers.get("content-encoding") == "gzip":
                body = gzip.decompress(body)

            body_json = json.loads(body.decode("utf-8"))
            return body_json
        except Exception as e:
            self.__logger.error(f"Failed to parse body: {e}")
            raise

    def _compare_content_length(
        self, node_response_raw: bytes, trusted_response_raw: bytes
    ) -> bool:
        headers_node = self.__parse_headers(node_response_raw)
        headers_trusted = self.__parse_headers(trusted_response_raw)
        node_length = headers_node.get("content-length")
        trusted_length = headers_trusted.get("content-length")

        if node_length != trusted_length:
            self.__logger.warning(
                f"Content-length mismatch: node({node_length}) vs trusted({trusted_length})"
            )
            return False

        return True

    def _compare_body_size(
        self, node_response_raw: bytes, trusted_response_raw: bytes
    ) -> bool:
        body_node = node_response_raw.split(b"\r\n\r\n", 1)[1]
        body_trusted = trusted_response_raw.split(b"\r\n\r\n", 1)[1]

        if len(body_node) != len(body_trusted):
            self.__logger.warning(
                f"Body size mismatch: node({len(body_node)}) vs trusted({len(body_trusted)})"
            )
            return False

        return True

    def _compare_body_content(
        self, node_response_raw: bytes, trusted_response_raw: bytes
    ) -> bool:
        headers_node = self.__parse_headers(node_response_raw)
        headers_trusted = self.__parse_headers(trusted_response_raw)
        body_node = self.__parse_body(node_response_raw, headers_node)
        body_trusted = self.__parse_body(trusted_response_raw, headers_trusted)

        # TODO: implement more sophisticated comparisons..
        if body_node != body_trusted:
            self.__logger.warning(
                f"Body mismatch: node({json.dumps(body_node)}) vs trusted({json.dumps(body_trusted)})"
            )
            return False

        return True
