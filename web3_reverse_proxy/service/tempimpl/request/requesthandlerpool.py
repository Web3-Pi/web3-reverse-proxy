from service.tempimpl.requesthandler import RequestHandler


class RequestHandlerPool:

    def __init__(self, endpoint: str, port: int, name: str):
        self.ready_to_use = []
        self.in_use = set()

        self.endpoint = endpoint
        self.port = port
        self.name = name

    def get(self) -> RequestHandler:
        if len(self.ready_to_use) > 0:
            elt = self.ready_to_use.pop()
            self.in_use.add(elt)

            return elt
        else:
            elt = RequestHandler(self.endpoint, self.port, self.name)
            self.in_use.add(elt)

            return elt

    def release(self, rh: RequestHandler) -> None:
        self.ready_to_use.append(rh)
        self.in_use.remove(rh)
