# TODO: Apply locks to prevent data loss and inconsistency
# from threading import Lock, RLock
from typing import Any, Dict, Optional

from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest


class CallStats:

    REQ_BYTES = "request_bytes"
    RESP_BYTES = "response_bytes"
    TOTAL_BYTES = "total_bytes"
    NUM_CALLS = "num_calls"

    def __init__(self, _rqb: int = 0, _rsb: int = 0) -> None:
        self.req_bytes = _rqb
        self.resp_bytes = _rsb
        self.num_calls = 0

        # self.__lock = RLock()

    def update(self, req_bytes: int, resp_bytes: int, num_calls: int) -> None:
        # with self.__lock:
        self.req_bytes += req_bytes
        self.resp_bytes += resp_bytes
        self.num_calls += num_calls

    def total_bytes_processed(self) -> int:
        # with self.__lock:
        return self.req_bytes + self.resp_bytes

    def to_dict(self) -> Dict[str, Any]:
        # with self.__lock:
        return {
            self.NUM_CALLS: self.num_calls,
            self.TOTAL_BYTES: self.total_bytes_processed(),
            self.REQ_BYTES: self.req_bytes,
            self.RESP_BYTES: self.resp_bytes,
        }


class UserActivitySummary:
    CALLS_STATS = "calls_stats"
    TOTAL_NUM_BYTES = "total_num_bytes"
    TOTAL_NUM_CALLS = "total_num_calls"

    def __init__(self) -> None:
        self.calls_stats = {}

        self.total_request_bytes = 0
        self.total_response_bytes = 0
        self.total_num_calls = 0

        # self.__lock = RLock()

    def update(
        self, method: str, req_bytes: int, resp_bytes: int, num_calls: int
    ) -> None:
        # with self.__lock:
        if method not in self.calls_stats:
            self.calls_stats[method] = CallStats()

        self.calls_stats[method].update(req_bytes, resp_bytes, num_calls)

        self.total_num_calls += num_calls
        self.total_request_bytes += req_bytes
        self.total_response_bytes += resp_bytes

    def total_bytes_processed(self) -> int:
        # with self.__lock:
        return self.total_request_bytes + self.total_response_bytes

    def to_dict(self) -> dict:
        # with self.__lock:
        return {
            self.CALLS_STATS: {k: v.to_dict() for k, v in self.calls_stats.items()},
            self.TOTAL_NUM_CALLS: self.total_num_calls,
            self.TOTAL_NUM_BYTES: self.total_request_bytes + self.total_response_bytes,
        }


class ServiceActivitySummary:

    def __init__(self) -> None:
        self.users_summaries = {}
        # self.__lock = Lock()

    def add_new_user(self, user_api_key: str) -> None:
        self._get_or_create_uas(user_api_key)

    def remove_user(self, user_api_key: str) -> None:
        # with self.__lock:
        if user_api_key in self.users_summaries:
            del self.users_summaries[user_api_key]

    def _get_or_create_uas(self, user_api_key: str) -> UserActivitySummary:
        # with self.__lock:
        if user_api_key not in self.users_summaries:
            self.users_summaries[user_api_key] = UserActivitySummary()

        return self.users_summaries[user_api_key]

    def get_user_activity_summary(
        self, user_api_key: str
    ) -> Optional[UserActivitySummary]:
        res = None
        # with self.__lock:
        if user_api_key in self.users_summaries:
            res = self.users_summaries[user_api_key]

        return res

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

        uas_entry = self._get_or_create_uas(request.user_api_key)
        uas_entry.update(request.method, req_bytes, len(response), num_calls)

    def to_dict(self) -> Dict[str, Any]:
        # with self.__lock:
        return {k: v.to_dict() for k, v in self.users_summaries.items()}
