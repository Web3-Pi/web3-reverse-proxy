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

    PROXY_ERROR_BASE_CODE = 666000

    PE_HEADERS_OFFSET = 100
    PE_INVALID_FORMAT_OFFSET = 200
    PE_MISSING_METHOD_OFFSET = 300
    PE_INVALID_API_KEY_OFFSET = 1100
    PE_PAYMENT_REQUIRED = 2005
    PE_PAYLOAD_TOO_LARGE = 3100
    PE_SERVICE_UNAVAILABLE = 7100

    SERVER_ERROR_TEMPLATE = 'HTTP/1.1 {} {}\r\nContent-Type: text/plain\r\nContent-Length: {}\r\n\r\n{}\n'

    BASIC_RESPONSE_TEMPLATE = 'HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nDate: {}\r\nContent-Length: {' \
                              '}\r\n\r\n{}\n'

    UNAUTH_RESPONSE_TEMPLATE = 'HTTP/1.1 401 Unauthorized\r\nContent-Type: text/plain; charset=utf-8\r\nDate: {}\r\n' \
                               'Content-Length: {}\r\nConnection: keep-alive\r\nVary: Origin\r\nWww-Authenticate: ' \
                               'Basic realm="Auth failure, invalid authentication id"\r\nX-Content-Type-Options: ' \
                               'nosniff\r\n\r\n{}\n'

    WEB3_JSON_TEMPLATE = '{{"jsonrpc":"2.0","id":{}}},"error":{{"code":{},"message":"{}"}}}}'

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
    def bad_request_web3(cls, code_req: int, code_web3: int, message: str, _id: int | str = "null") -> bytes:
        _err_code = code_req
        _err_msg = cls.ERROR_CODES[_err_code]
        _now = cls.current_datetime()
        _json = cls.web3_json(code_web3, message, _id)
        _len = len(cls.to_bytes(_json)) + 1  # +1 to include \n from the template

        err_msg = cls.BASIC_RESPONSE_TEMPLATE.format(_err_code, _err_msg, _now, _len, _json)

        return cls.to_bytes(err_msg)

    @classmethod
    def bad_request_headers(cls) -> bytes:
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_HEADERS_OFFSET)
        return cls.bad_request_web3(400, web3_err, "Too many headers")

    @classmethod
    def bad_request_missing_method(cls) -> bytes:
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_MISSING_METHOD_OFFSET)
        return cls.bad_request_web3(400, web3_err, "Missing method field")

    @classmethod
    def bad_request_invalid_request_format(cls):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_INVALID_FORMAT_OFFSET)
        return cls.bad_request_web3(400, web3_err, "Invalid request format")

    @classmethod
    def unauthorized_invalid_API_key(cls):
        _now = cls.current_datetime()
        _data = 'invalid authentication id'
        _len = len(_data) + 1  # +1 to include \n from the template
        err_msg = cls.UNAUTH_RESPONSE_TEMPLATE.format(_now, _len, _data)

        return cls.to_bytes(err_msg)

    @classmethod
    def forbidden_payment_required(cls):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_PAYMENT_REQUIRED)
        return cls.bad_request_web3(429, web3_err, "You exceeded the limit of calls. Check your plan")

    @classmethod
    def payload_too_large(cls):
        web3_err = -(cls.PROXY_ERROR_BASE_CODE + cls.PE_PAYLOAD_TOO_LARGE)
        return cls.bad_request_web3(413, web3_err, "Request payload too large")

    @classmethod
    def internal_server_error(cls):
        _data = "Something broke, no worries, it is a PoC"
        _len = len(_data) + 1  # +1 to include \n from the template

        err_msg = cls.SERVER_ERROR_TEMPLATE.format(500, "Internal Server Error", _len, _data)

        return cls.to_bytes(err_msg)

    @classmethod
    def service_unavailable(cls):
        _data = "System overload of sorts (proxy run out of resources???). Try again in a few minutes"
        _len = len(_data) + 1  # +1 to include \n from the template

        err_msg = cls.SERVER_ERROR_TEMPLATE.format(503, "Service Unavailable", _len, _data)

        return cls.to_bytes(err_msg)
