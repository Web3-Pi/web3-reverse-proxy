from collections import OrderedDict

from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware


class RequestMiddlewareDescr:

    def __init__(self) -> None:
        self.middlewares = OrderedDict()

    def append(self, middleware_class, *args) -> None:
        self.middlewares[middleware_class] = args

    def is_empty(self) -> bool:
        return len(self.middlewares) == 0

    def clear(self) -> None:
        self.middlewares = OrderedDict()

    def instantiate(self) -> RequestReaderMiddleware:
        next_middleware = None

        for middleware_class in reversed(self.middlewares.keys()):
            args = self.middlewares[middleware_class]
            next_middleware = middleware_class(next_middleware, *args)

        return next_middleware
