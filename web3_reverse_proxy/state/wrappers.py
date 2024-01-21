from typing import Callable

from web3_reverse_proxy.interfaces.permissions import CallPermissions, ClientPermissions
from web3_reverse_proxy.service.billing.billingservice import BasicBillingService
from web3_reverse_proxy.service.ledger.activitysummary import UserActivitySummary


class BasicBillingServiceWithLedger(CallPermissions):

    def __init__(self, billing: BasicBillingService, fun_get_user_summary: Callable[[str], UserActivitySummary]) -> None:
        self.billing_service = billing
        self.get_user_summary_fun = fun_get_user_summary

    # FIXME: priorities and GLM settlements should also be verified here (although they should be read only when
    #  necessary, and definitely not every time rpc call is invoked by user
    def is_allowed(self, user_api_key: str, method: str) -> bool:
        user_summary = self.get_user_summary_fun(user_api_key)

        num_calls_so_far = 0
        num_bytes_so_far = 0

        if user_summary is not None:
            num_calls_so_far = user_summary.total_num_calls
            num_bytes_so_far = user_summary.total_bytes_processed()

        return self.billing_service.is_allowed(user_api_key, method, num_calls_so_far, num_bytes_so_far)

    def get_call_priority(self, user_api_key: str, method: str) -> int:
        return self.billing_service.get_call_priority(user_api_key, method)


class SimpleAuthenticatorFromBilling(ClientPermissions):
    def __init__(self, billing: BasicBillingService) -> None:
        self.billing_service = billing

    def is_authorized(self, user_api_key: str) -> bool:
        return self.billing_service.is_registered(user_api_key)
