from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class OptionsResponses:

    BASIC_RESPONSE_TEMPLATE = (
        b"HTTP/1.1 200 OK\r\n"
        b"Access-Control-Allow-Headers: Content-Type\r\n"
        b"Access-Control-Allow-Methods: POST, OPTIONS\r\n"
        b"Access-Control-Allow-Origin: *\r\n"
        b"Content-Length: 0\r\n"
        b"\r\n"
    )

    @classmethod
    def options_response(cls, req: RPCRequest):
        return cls.BASIC_RESPONSE_TEMPLATE
