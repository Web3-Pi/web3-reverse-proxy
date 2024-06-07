class JSONRPCError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class InvalidRequestError(JSONRPCError):
    def __init__(self, msg: str) -> None:
        super().__init__(-32600, msg)


class MethodNotFoundError(JSONRPCError):
    def __init__(self, msg: str):
        super().__init__(-32601, msg)


class InvalidParamsError(JSONRPCError):
    def __init__(self, msg: str):
        super().__init__(-32602, msg)
