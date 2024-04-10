from email.utils import formatdate


class ErrorResponses:

    # FIXME: json responses should contain a valid id sent in the corresponding request, right now "null" id is returned
    #  by default
    ERROR_CODES = {400: 'Bad Request',
                   401: 'Unauthorized',
                   403: 'Forbidden',
                   410: 'Gone',
                   413: 'Payload Too Large',
                   429: 'Too Many Requests',
                   500: 'Internal Server Error',
                   503: 'Service Unavailable'
                   }

    SERVER = "rpi_servix/0.0.1"

    PROXY_ERROR_BASE_CODE = 32000

    PE_HEADERS_OFFSET = 1
    PE_INVALID_FORMAT_OFFSET = 2
    PE_PAYMENT_REQUIRED = 3
    PE_PAYLOAD_TOO_LARGE = 4

    SERVER_ERROR_TEMPLATE = 'HTTP/1.1 {} {}\r\nContent-Type: text/plain\r\nContent-Length: {}\r\n\r\n{}\n'

    BASIC_RESPONSE_TEMPLATE = 'HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nDate: {}\r\nContent-Length: {' \
                              '}\r\n\r\n{}\n'

    UNAUTH_RESPONSE_TEMPLATE = 'HTTP/1.1 401 Unauthorized\r\nContent-Type: text/plain; charset=utf-8\r\nDate: {}\r\n' \
                               'Content-Length: {}\r\nConnection: keep-alive\r\nVary: Origin\r\nWww-Authenticate: ' \
                               'Basic realm="Auth failure, invalid authentication id"\r\nX-Content-Type-Options: ' \
                               'nosniff\r\n\r\n{}\n'

    WEB3_JSON_TEMPLATE = '{{"jsonrpc":"2.0","id":{},"error":{{"code":{},"message":"{}"}}}}'

    @classmethod
    def to_bytes(cls, data: str) -> bytes:
        return bytes(data, "utf-8")

    @classmethod
    def current_datetime(cls) -> str:
        return formatdate(timeval=None, localtime=False, usegmt=True)

    @classmethod
    def web3_json(cls, code: int, message: str, _id: int | str):
        return cls.WEB3_JSON_TEMPLATE.format(_id, code, message)

    @classmethod
    def bad_request_web3(cls, code_web3: int, message: str, _id: int | str = None) -> bytes:
        _err_msg = "OK"
        _now = cls.current_datetime()
        _json = cls.web3_json(code_web3, message, _id or "null")
        _len = len(cls.to_bytes(_json)) + 1  # +1 to include \n from the template

        err_msg = cls.BASIC_RESPONSE_TEMPLATE.format(200, _err_msg, _now, _len, _json)

        return cls.to_bytes(err_msg)

    @classmethod
    def bad_request_headers(cls, _id: int | str = None) -> bytes:
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_HEADERS_OFFSET)
        return cls.bad_request_web3(web3_err, "Too many headers", _id)

    @classmethod
    def bad_request_invalid_request_format(cls, _id: int | str = None):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_INVALID_FORMAT_OFFSET)
        return cls.bad_request_web3(web3_err, "Invalid request format", _id)

    @classmethod
    def unauthorized_invalid_API_key(cls):
        _now = cls.current_datetime()
        _data = 'invalid authentication id'
        _len = len(_data) + 1  # +1 to include \n from the template
        err_msg = cls.UNAUTH_RESPONSE_TEMPLATE.format(_now, _len, _data)

        return cls.to_bytes(err_msg)

    @classmethod
    def forbidden_payment_required(cls, _id: int | str = None):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_PAYMENT_REQUIRED)
        return cls.bad_request_web3(web3_err, "You exceeded the limit of calls. Check your plan", _id)

    @classmethod
    def payload_too_large(cls, _id: int | str = None):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_PAYLOAD_TOO_LARGE)
        return cls.bad_request_web3(web3_err, "Request payload too large", _id)

    @classmethod
    def internal_server_error(cls):
        _data = ""
        _len = len(_data) + 1  # +1 to include \n from the template

        err_msg = cls.SERVER_ERROR_TEMPLATE.format(500, "Internal Server Error", _len, _data)

        return cls.to_bytes(err_msg)

    @classmethod
    def service_unavailable(cls):
        _data = "System overload of sorts (proxy run out of resources???). Try again in a few minutes"
        _len = len(_data) + 1  # +1 to include \n from the template

        err_msg = cls.SERVER_ERROR_TEMPLATE.format(503, "Service Unavailable", _len, _data)

        return cls.to_bytes(err_msg)

    @classmethod
    def parse_error(cls, _id: int | str = None):
        return cls.bad_request_web3(-32700, "Invalid JSON format", _id)
