from datetime import datetime
from typing import Dict

from web3pi_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3pi_proxy.interfaces.servicestate import StateUpdater
from web3pi_proxy.service.ledger.activitysummary import (
    ServiceActivitySummary,
    UserActivitySummary,
)

# from threading import Lock


# TODO: Apply locks to prevent data loss and inconsistency
class SimpleActivityLedger(StateUpdater):

    ALL_TIME_SUMMARY = "all_time_summary"
    DAILY_USE_SUMMARY = "daily_use_summary"

    daily_usage: Dict[str, ServiceActivitySummary]
    all_time_summary: ServiceActivitySummary

    def __init__(self):
        self.daily_usage = {}
        self.all_time_summary = ServiceActivitySummary()

        # self.__lock = Lock()

    @staticmethod
    def utc_now_as_key() -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")

    def get_all_time_user_summary(self, user_api_key: str) -> UserActivitySummary:
        return self.all_time_summary.get_user_activity_summary(user_api_key)

    def get_active_state_sample(self) -> ServiceActivitySummary:
        key = self.utc_now_as_key()

        # with self.__lock:
        if key not in self.daily_usage:
            self.daily_usage[key] = ServiceActivitySummary()

        return self.daily_usage[key]

    def remove_user(self, user_api_key: str) -> None:
        self.all_time_summary.remove_user(user_api_key)
        # with self.__lock:
        for daily_summary in self.daily_usage.values():
            daily_summary.remove_user(user_api_key)

    def record_rpc_request(self, request: RPCRequest) -> None:
        sample = self.get_active_state_sample()
        sample.update(request=request)
        self.all_time_summary.update(request=request)

    def record_rpc_response(self, request: RPCRequest, response: bytearray) -> None:
        sample = self.get_active_state_sample()
        sample.update(request=request, response=response, response_only=True)
        self.all_time_summary.update(
            request=request, response=response, response_only=True
        )

    def get_all_time_summary(self) -> ServiceActivitySummary:
        return self.all_time_summary

    def to_dict(self) -> dict:
        # with self.__lock:
        return {
            self.ALL_TIME_SUMMARY: self.get_all_time_summary().to_dict(),
            self.DAILY_USE_SUMMARY: {
                k: v.to_dict() for k, v in self.daily_usage.items()
            },
        }
