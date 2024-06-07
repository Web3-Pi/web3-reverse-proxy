from collections import OrderedDict
from io import StringIO
from typing import Any, Dict

from web3_reverse_proxy.core.rpc.node.rpcendpoint.connection.endpointconnectionstats import (
    EndpointConnectionStats,
)
from web3_reverse_proxy.core.stats.proxystats import RPCProxyStats
from web3_reverse_proxy.service.billing.billingplan import SimplestBillingPlan
from web3_reverse_proxy.service.billing.billingservice import BasicBillingService
from web3_reverse_proxy.service.http.rpcadmincalls import RPCAdminCalls
from web3_reverse_proxy.service.ledger.activityledger import SimpleActivityLedger


class RPCServiceAdmin:

    CONSOLE_CONTENTS = "console_contents"

    USERS_API_KEYS = "users_api_keys"

    ReturnType = Dict[str, Any] | None

    def __init__(
        self,
        billing: BasicBillingService,
        activity: SimpleActivityLedger,
        console_buffer: StringIO,
    ):
        self.billing_service = billing
        self.activity_ledger = activity
        self.console_buffer = console_buffer
        self.proxy_stats = None
        self.endpoint_stats = OrderedDict()

        self.mapping = {
            RPCAdminCalls.QUERY_USER_PLAN: self.query_user_plan,
            RPCAdminCalls.QUERY_USER_STATE: self.query_user_state,
            RPCAdminCalls.QUERY_LIST_REGISTERED_USERS: self.query_list_registered_users,
            RPCAdminCalls.QUERY_LIST_USERS_ACTIVITIES_BASIC: self.query_list_users_activities_basic,
            RPCAdminCalls.QUERY_LIST_USERS_ACTIVITIES_DETAILED: self.query_list_users_activities_detailed,
            RPCAdminCalls.REGISTER_USER: self.register_user_flat,
            RPCAdminCalls.REMOVE_USER: self.remove_user,
            RPCAdminCalls.UPDATE_USER_PLAN: self.update_user_plan_flat,
            RPCAdminCalls.QUERY_PROXY_STATS: self.query_proxy_stats,
            RPCAdminCalls.QUERY_LIST_ENDPOINTS: self.query_list_endpoints,
            RPCAdminCalls.QUERY_ENDPOINT_STATS: self.query_endpoint_stats,
            RPCAdminCalls.QUERY_SERVICE_CONSOLE: self.query_service_console,
        }

    @classmethod
    def create_plan(
        cls, free_calls: int | str, free_bytes: int | str, priority: int | str
    ):
        # FIXME: naive type handling
        free_calls_num = int(free_calls)
        free_bytes_num = int(free_bytes)
        priority = int(priority)

        return SimplestBillingPlan(free_calls_num, free_bytes_num, 0.0, 0.0, priority)

    @classmethod
    def as_dict(cls, entry) -> Dict[str, Any]:
        if entry is not None:
            return entry.to_dict()

        return {}

    def register_proxy_stats(self, stats: RPCProxyStats) -> None:
        self.proxy_stats = stats

    def register_endpoint_stats(
        self, name: str, stats: EndpointConnectionStats
    ) -> None:
        assert name not in self.endpoint_stats

        self.endpoint_stats[name] = stats

    def set_console_buffer(self, console_buffer: StringIO):
        self.console_buffer = console_buffer

    def clear_transient_fields(self):
        self.proxy_stats = None
        self.console_buffer = None
        self.endpoint_stats = OrderedDict()

    def is_user_registered(self, user_api_key: str) -> bool:
        return self.billing_service.is_registered(user_api_key)

    # #########################################################
    # #                USER DOMAIN QUERIES                    #
    # #########################################################
    def query_user_plan(self, user_api_key: str) -> ReturnType:
        res = self.billing_service.get_user_plan(user_api_key)

        return self.as_dict(res)

    def query_user_state(self, user_api_key: str) -> ReturnType:
        res = self.activity_ledger.get_all_time_user_summary(user_api_key)

        return self.as_dict(res)

    def query_list_registered_users(self) -> ReturnType:
        users_api_keys = self.billing_service.get_registered_users_api_keys()

        return {self.USERS_API_KEYS: users_api_keys}

    def query_list_users_activities_basic(self) -> ReturnType:
        res = self.activity_ledger.get_all_time_summary()

        return self.as_dict(res)

    def query_list_users_activities_detailed(self) -> ReturnType:
        return self.as_dict(self.activity_ledger)

    def register_user(
        self, user_api_key: str, user_plan: SimplestBillingPlan
    ) -> ReturnType:
        if not self.billing_service.is_registered(user_api_key):
            self.billing_service.register_user(user_api_key, user_plan)

            return self.query_list_registered_users()

    def register_user_flat(
        self, user_api_key: str, free_calls: int, free_bytes: int, priority: int
    ) -> ReturnType:
        return self.register_user(
            user_api_key, self.create_plan(free_calls, free_bytes, priority)
        )

    def remove_user(self, user_api_key: str) -> ReturnType:
        if self.billing_service.is_registered(user_api_key):
            self.billing_service.remove_user(user_api_key)
            self.activity_ledger.remove_user(user_api_key)

            return self.query_list_registered_users()

    def update_user_plan(
        self, user_api_key: str, user_plan: SimplestBillingPlan
    ) -> ReturnType:
        if self.billing_service.is_registered(user_api_key):
            self.billing_service.update_user_plan(user_api_key, user_plan)

            return self.query_user_plan(user_api_key)

    def update_user_plan_flat(
        self, user_api_key: str, free_calls: int, free_bytes: int, priority: int
    ) -> ReturnType:
        return self.update_user_plan(
            user_api_key, self.create_plan(free_calls, free_bytes, priority)
        )

    # #########################################################
    # #                PROXY DOMAIN QUERIES                   #
    # #########################################################
    def query_proxy_stats(self) -> ReturnType:
        return self.as_dict(self.proxy_stats)

    def query_list_endpoints(self) -> ReturnType:
        return {k: self.as_dict(v) for k, v in self.endpoint_stats.items()}

    def query_endpoint_stats(self, endpoint_name: str) -> ReturnType:
        if endpoint_name in self.endpoint_stats:
            return self.as_dict(self.endpoint_stats[endpoint_name])

        return {}

    # #########################################################
    # #                SERVICE DOMAIN QUERIES                 #
    # #########################################################

    def query_service_console(self) -> ReturnType:
        return {self.CONSOLE_CONTENTS: self.console_buffer.getvalue()}

    # FIXME: parameter type handling should be implemented in a more generic way
    def call_by_method(self, method: str, params: list) -> ReturnType:
        return self.mapping[method](*params) if method in self.mapping else None
