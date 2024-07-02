from email.utils import formatdate


class ErrorResponses:

    # FIXME: json responses should contain a valid id sent in the corresponding request, right now "null" id is returned
    #  by default

    # TODO: Review and remove unused error codes for HTTP and JSON-RPC
    ERROR_CODES = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        405: "Method Not Allowed",
        410: "Gone",
        413: "Payload Too Large",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }

    SERVER = "rpi_servix/0.0.1"

    PROXY_ERROR_BASE_CODE = 32000

    PE_HEADERS_OFFSET = 1
    PE_INVALID_FORMAT_OFFSET = 2
    PE_PAYMENT_REQUIRED = 3
    PE_PAYLOAD_TOO_LARGE = 4

    HTTP_ERROR_TEMPLATE = (
        "HTTP/1.1 {} {}\r\nContent-Type: text/plain\r\nContent-Length: {}\r\n\r\n{}\n"
    )

    BASIC_RESPONSE_TEMPLATE = (
        "HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nDate: {}\r\nContent-Length: {"
        "}\r\n\r\n{}\n"
    )

    UNAUTH_RESPONSE_TEMPLATE = (
        "HTTP/1.1 401 Unauthorized\r\nContent-Type: text/plain; charset=utf-8\r\nDate: {}\r\n"
        "Content-Length: {}\r\nConnection: keep-alive\r\nVary: Origin\r\nWww-Authenticate: "
        'Basic realm="Auth failure, invalid authentication id"\r\nX-Content-Type-Options: '
        "nosniff\r\n\r\n{}\n"
    )

    WEB3_JSON_TEMPLATE = (
        '{{"jsonrpc":"2.0","id":{},"error":{{"code":{},"message":"{}"}}}}'
    )

    @classmethod
    def http_error(cls, code: int, message: str = "") -> bytes:
        length = len(message) + 1
        error = cls.ERROR_CODES[code]
        err_msg = cls.HTTP_ERROR_TEMPLATE.format(code, error, length, message)
        return cls.to_bytes(err_msg)

    @classmethod
    def to_bytes(cls, data: str) -> bytes:
        return bytes(data, "utf-8")

    @classmethod
    def current_datetime(cls) -> str:
        return formatdate(timeval=None, localtime=False, usegmt=True)

    @classmethod
    def web3_json(cls, code: int, message: str, _id: int | str) -> str:
        return cls.WEB3_JSON_TEMPLATE.format(_id, code, message)

    @classmethod
    def bad_request_web3(
        cls, code_web3: int, message: str, _id: int | str = None
    ) -> bytes:
        _err_msg = "OK"
        _now = cls.current_datetime()
        _json = cls.web3_json(code_web3, message, _id or "null")
        _len = len(cls.to_bytes(_json)) + 1  # +1 to include \n from the template

        err_msg = cls.BASIC_RESPONSE_TEMPLATE.format(200, _err_msg, _now, _len, _json)

        return cls.to_bytes(err_msg)

    @classmethod
    def forbidden_payment_required(cls, _id: int | str = None) -> bytes:
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_PAYMENT_REQUIRED)
        return cls.bad_request_web3(
            web3_err, "You exceeded the limit of calls. Check your plan", _id
        )

    @classmethod
    def parse_error(cls, _id: int | str = None) -> bytes:
        return cls.bad_request_web3(-32700, "Invalid JSON format", _id)

    @classmethod
    def connection_error(cls, _id: int | str = None) -> bytes:
        return cls.bad_request_web3(-32603, "Could not reach server", _id)

    @classmethod
    def http_internal_server_error(cls) -> bytes:
        return cls.http_error(500)

    @classmethod
    def http_service_unavailable(cls) -> bytes:
        return cls.http_error(
            503,
            "System overload of sorts (proxy run out of resources???). Try again in a few minutes",
        )

    @classmethod
    def http_bad_request(cls, message: str = "") -> bytes:
        return cls.http_error(400, message)

    @classmethod
    def http_method_not_allowed(cls) -> bytes:
        return cls.http_error(405, "Only POST requests are accepted")

    @classmethod
    def unauthorized_invalid_API_key(cls) -> bytes:
        _now = cls.current_datetime()
        _data = "invalid authentication id"
        _len = len(_data) + 1
        err_msg = cls.UNAUTH_RESPONSE_TEMPLATE.format(_now, _len, _data)

        return cls.to_bytes(err_msg)
