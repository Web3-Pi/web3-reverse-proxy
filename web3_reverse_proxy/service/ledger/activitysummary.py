from typing import Dict, Any

from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class CallStats:

    REQ_BYTES = "request_bytes"
    RESP_BYTES = "response_bytes"
    TOTAL_BYTES = "total_bytes"
    NUM_CALLS = "num_calls"

    def __init__(self, _rqb: int = 0, _rsb: int = 0):
        self.req_bytes = _rqb
        self.resp_bytes = _rsb
        self.num_calls = 0

    def update(self, req_bytes: int, resp_bytes: int):
        self.req_bytes += req_bytes
        self.resp_bytes += resp_bytes
        self.num_calls += 1

    def total_bytes_processed(self):
        return self.req_bytes + self.resp_bytes

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.NUM_CALLS: self.num_calls,
            self.TOTAL_BYTES: self.total_bytes_processed(),
            self.REQ_BYTES: self.req_bytes,
            self.RESP_BYTES: self.resp_bytes
        }


class UserActivitySummary:
    CALLS_STATS = 'calls_stats'
    TOTAL_NUM_BYTES = 'total_num_bytes'
    TOTAL_NUM_CALLS = 'total_num_calls'

    def __init__(self):
        self.calls_stats = {}

        self.total_request_bytes = 0
        self.total_response_bytes = 0
        self.total_num_calls = 0

    def register_next_call(self, method: str, req_bytes: int, resp_bytes: int) -> None:
        if method not in self.calls_stats:
            self.calls_stats[method] = CallStats()

        self.calls_stats[method].update(req_bytes, resp_bytes)

        self.total_num_calls += 1
        self.total_request_bytes += req_bytes
        self.total_response_bytes += resp_bytes

    def total_bytes_processed(self):
        return self.total_request_bytes + self.total_response_bytes

    def to_dict(self) -> dict:
        return {
            self.CALLS_STATS: {k: v.to_dict() for k, v in self.calls_stats.items()},
            self.TOTAL_NUM_CALLS: self.total_num_calls,
            self.TOTAL_NUM_BYTES: self.total_request_bytes + self.total_response_bytes
        }


class ServiceActivitySummary:

    def __init__(self):
        self.users_summaries = {}

    def add_new_user(self, user_api_key: str) -> None:
        self._get_or_create_uas(user_api_key)

    def remove_user(self, user_api_key: str) -> None:
        if user_api_key in self.users_summaries:
            del self.users_summaries[user_api_key]

    def _get_or_create_uas(self, user_api_key: str) -> UserActivitySummary:
        if user_api_key not in self.users_summaries:
            self.users_summaries[user_api_key] = UserActivitySummary()

        return self.users_summaries[user_api_key]

    def get_user_activity_summary(self, user_api_key: str) -> UserActivitySummary | None:
        res = None
        if user_api_key in self.users_summaries:
            res = self.users_summaries[user_api_key]

        return res

    def register_next_call(self, request: RPCRequest, response: RPCResponse) -> None:
        uas_entry = self._get_or_create_uas(request.user_api_key)
        uas_entry.register_next_call(request.method, len(request.last_queried_bytes), len(response.data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            k: v.to_dict() for k, v in self.users_summaries.items()
        }
