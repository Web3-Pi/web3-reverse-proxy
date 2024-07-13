# TODO: Apply locks to prevent data loss and inconsistency
# from threading import Lock, RLock
from typing import Any, Dict, Optional

from web3pi_proxy.db.models import User, CallStats
from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class UserActivitySummary:
    CALLS_STATS = "calls_stats"
    TOTAL_NUM_BYTES = "total_num_bytes"
    TOTAL_NUM_CALLS = "total_num_calls"

    user: Optional[User]
    method_stats: Dict[str, CallStats]
    total_stats: CallStats

    def __init__(self, user: Optional[User]) -> None:
        self.user = user
        self.total_stats = CallStats(user=User, method=None)
        self.method_stats = {}

        # self.__lock = RLock()

    def __repr__(self):
       return f"<{self.__class__.__name__}: user={self.user}>"

    def update(
        self, method: str, req_bytes: int, resp_bytes: int, num_calls: int
    ) -> None:
        # with self.__lock:
        if method not in self.method_stats:
            self.method_stats[method] = CallStats(user=self.user, method=method)

        self.method_stats[method].update_stats(req_bytes, resp_bytes, num_calls)
        self.total_stats.update_stats(req_bytes, resp_bytes, num_calls)

    def to_dict(self) -> dict:
        # with self.__lock:
        return {
            self.CALLS_STATS: {k: v.to_dict() for k, v in self.method_stats.items()},
            self.TOTAL_NUM_CALLS: self.total_stats.num_calls,
            self.TOTAL_NUM_BYTES: self.total_stats.total_bytes,
        }


class ServiceActivitySummary:
    user_summaries: Dict[str, UserActivitySummary]

    def __init__(self) -> None:
        self.user_summaries = {}
        # self.__lock = Lock()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.user_summaries}>"

    def add_new_user(self, user_api_key: str) -> None:
        self._get_or_create_uas(user_api_key)

    def remove_user(self, user_api_key: str) -> None:
        # with self.__lock:
        self.user_summaries.pop(user_api_key, None)

    def _get_or_create_uas(self, user_api_key: str) -> UserActivitySummary:
        # with self.__lock:
        return self.user_summaries.setdefault(user_api_key, UserActivitySummary(None))

    def get_user_activity_summary(
        self, user_api_key: str
    ) -> Optional[UserActivitySummary]:
        return self.user_summaries.get(user_api_key)

    def update(
        self,
        request: RPCRequest,
        response: bytearray = bytearray(),
        response_only: bool = False,
    ) -> None:
        if response_only:
            num_calls = 0
            req_bytes = 0
        else:
            num_calls = 1
            req_bytes = len(request.last_queried_bytes)

        if request.user_api_key:  # in the ProxyMode.SIM there can be no user context
            uas_entry = self._get_or_create_uas(request.user_api_key)
            uas_entry.update(request.method, req_bytes, len(response), num_calls)

    def to_dict(self) -> Dict[str, Any]:
        # with self.__lock:
        return {k: v.to_dict() for k, v in self.user_summaries.items()}
