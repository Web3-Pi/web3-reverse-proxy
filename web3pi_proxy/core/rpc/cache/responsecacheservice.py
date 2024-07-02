from abc import ABC

from web3pi_proxy.core.rpc.cache.cacheservice import ExpirableCacheService
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class ResponseCacheService(ExpirableCacheService, ABC):
    def __init__(self, expiry_milis: int) -> None:
        super().__init__(expiry_milis)

    def is_writeable(self, request: RPCRequest) -> bool:
        pass


class StaticRequestResponseCacheService(ResponseCacheService):
    _WRITEABLE_METHODS = [
        "web3_clientVersion",
        "net_version",
        "chain_id",
    ]

    def is_writeable(self, request: RPCRequest) -> bool:
        return request.method in self._WRITEABLE_METHODS
