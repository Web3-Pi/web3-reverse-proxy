from typing import Callable

from web3pi_proxy.interfaces.permissions import CallPermissions, ClientPermissions
from web3pi_proxy.service.billing.billingservice import BasicBillingService
from web3pi_proxy.service.ledger.activitysummary import UserActivitySummary


class BasicBillingServiceWithLedger(CallPermissions):

    def __init__(
        self,
        billing: BasicBillingService,
        fun_get_user_summary: Callable[[str], UserActivitySummary],
    ) -> None:
        self.billing_service = billing
        self.get_user_summary_fun = fun_get_user_summary

    # FIXME: priorities and GLM settlements should also be verified here (although they should be read only when
    #  necessary, and definitely not every time rpc call is invoked by user
    def is_allowed(self, user_api_key: str, method: str) -> bool:
        user_summary = self.get_user_summary_fun(user_api_key) or UserActivitySummary(None)

        return self.billing_service.is_allowed(
            user_api_key,
            method,
            user_summary.total_stats.num_calls,
            user_summary.total_stats.total_bytes,
        )

    def get_call_priority(self, user_api_key: str, method: str) -> int:
        return self.billing_service.get_call_priority(user_api_key, method)

    def get_user_constant_pool(self, user_api_key: str) -> str | None:
        return self.billing_service.get_user_constant_pool(user_api_key)


class SimpleAuthenticatorFromBilling(ClientPermissions):
    def __init__(self, billing: BasicBillingService) -> None:
        self.billing_service = billing

    def is_authorized(self, user_api_key: str) -> bool:
        return self.billing_service.is_registered(user_api_key)
