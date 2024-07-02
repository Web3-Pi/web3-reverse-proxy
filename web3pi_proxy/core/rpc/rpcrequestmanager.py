from typing import Iterable, List, Optional

from web3pi_proxy.core.interfaces.rpcnode import EndpointsHandler
from web3pi_proxy.core.interfaces.rpcrequest import RequestReaderMiddleware
from web3pi_proxy.core.interfaces.rpcresponse import RPCResponseHandler
from web3pi_proxy.core.rpc.cache.responsecacheservice import ResponseCacheService
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.core.sockets.clientsocket import ClientSocket


class RPCProxyRequestManager:

    def __init__(
        self,
        request_reader: RequestReaderMiddleware,
        endpoints_handler: EndpointsHandler,
        response_handler: RPCResponseHandler,
        cache_service: Optional[ResponseCacheService] = None,
    ) -> None:

        self.request_reader = request_reader
        self.endpoints_handler = endpoints_handler
        self.response_handler = response_handler

        self.active_sockets = []
        self.requests = {}
        self.responses = []
        self.errors = {}

        self.no_current_responses = 0

        self.response_cache = cache_service

    @property
    def is_cache_available(self) -> bool:
        return self.response_cache is not None

    def clear_state(self) -> None:
        self.active_sockets = []
        self.requests = {}
        self.responses = []
        self.errors = {}

    def read_requests(self, client_sockets: Iterable[ClientSocket]) -> None:
        assert (
            len(self.requests) == 0
            and len(self.responses) == 0
            and len(self.errors) == 0
        )

        for cs in client_sockets:
            req, err = self.request_reader.read_request(cs, RPCRequest())

            if req is not None:
                self.requests[cs] = req
            else:
                self.errors[cs] = err

    def read_cache(self) -> None:
        for cs, request in list(self.requests.items()):
            if self.response_cache.is_writeable(request):
                cached_response = self.response_cache.get(request.method)
                if cached_response is not None:
                    self.responses.append((cs, cached_response))
                    del self.requests[cs]

    def process_requests(self) -> None:
        for cs, request in self.requests.items():
            self.endpoints_handler.add_request(cs, request)

        if self.endpoints_handler.has_pending_requests():
            responses = self.endpoints_handler.process_pending_requests()
            for cs, response in responses:
                if (
                    self.is_cache_available
                    and self.response_cache.is_writeable(response.request)
                    and self.response_cache.get(response.request.method) is None
                ):
                    self.response_cache.store(response.request.method, response)
                self.responses.append((cs, response))

    def handle_responses(self) -> None:
        self.no_current_responses = 0

        for cs, response in self.responses:
            if self.response_handler.handle_response(cs, response):
                self.no_current_responses += 1
                self.active_sockets.append(cs)
            else:
                self.errors[cs] = None

    def handle_errors(self) -> List[ClientSocket]:
        # FIXME: unreliable, "best effort" error handling
        for cs, err in self.errors.items():
            try:
                if err is not None and cs.is_ready_write():
                    cs.send_all(err.raw)
            except IOError:
                pass
            except Exception:
                raise

        return list(self.errors.keys())

    def handle_requests(self, client_sockets: Iterable[ClientSocket]) -> None:
        self.clear_state()

        self.read_requests(client_sockets)
        if self.is_cache_available:
            self.read_cache()
        self.process_requests()
        self.handle_responses()
        self.handle_errors()

    def get_num_processed_requests(self):
        return self.no_current_responses

    def get_processed_sockets(self) -> Iterable[ClientSocket]:
        return self.active_sockets

    def get_sockets_to_close(self) -> Iterable[ClientSocket]:
        return list(self.errors.keys())

    def shut_down(self):
        self.endpoints_handler.close()
