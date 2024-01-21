from datetime import datetime

from web3_reverse_proxy.interfaces.servicestate import StateUpdater
from web3_reverse_proxy.service.ledger.activitysummary import ServiceActivitySummary, UserActivitySummary
from web3_reverse_proxy.core.rpc.request.rpcrequest import RPCRequest
from web3_reverse_proxy.core.rpc.response.rpcresponse import RPCResponse


class SimpleActivityLedger(StateUpdater):

    ALL_TIME_SUMMARY = 'all_time_summary'
    DAILY_USE_SUMMARY = 'daily_use_summary'

    def __init__(self):
        self.daily_usage = {}
        self.all_time_summary = ServiceActivitySummary()

    @staticmethod
    def utc_now_as_key():
        return datetime.utcnow().strftime('%Y-%m-%d')

    def get_all_time_user_summary(self, user_api_key: str) -> UserActivitySummary:
        return self.all_time_summary.get_user_activity_summary(user_api_key)

    def get_active_state_sample(self) -> ServiceActivitySummary:
        key = self.utc_now_as_key()

        if key not in self.daily_usage:
            self.daily_usage[key] = ServiceActivitySummary()

        return self.daily_usage[key]

    def remove_user(self, user_api_key: str) -> None:
        self.all_time_summary.remove_user(user_api_key)
        for daily_summary in self.daily_usage.values():
            daily_summary.remove_user(user_api_key)

    def record_processed_rpc_call(self, request: RPCRequest, response: RPCResponse) -> None:
        sample = self.get_active_state_sample()
        sample.register_next_call(request, response)

        self.all_time_summary.register_next_call(request, response)

    def get_all_time_summary(self) -> ServiceActivitySummary:
        return self.all_time_summary

    def to_dict(self) -> dict:
        return {
            self.ALL_TIME_SUMMARY: self.get_all_time_summary().to_dict(),
            self.DAILY_USE_SUMMARY: {k: v.to_dict() for k, v in self.daily_usage.items()}
        }
