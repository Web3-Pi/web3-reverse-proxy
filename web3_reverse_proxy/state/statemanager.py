import datetime
from io import StringIO
from typing import Iterable

from web3_reverse_proxy.core.rpc.node.rpcendpoint.endpointimpl import RPCEndpoint
from web3_reverse_proxy.core.stats.proxystats import RPCProxyStats
from web3_reverse_proxy.interfaces.permissions import CallPermissions, ClientPermissions
from web3_reverse_proxy.interfaces.servicestate import StateUpdater
from web3_reverse_proxy.service.admin.serviceadmin import RPCServiceAdmin
from web3_reverse_proxy.service.billing.billingservice import BasicBillingService
from web3_reverse_proxy.service.ledger.activityledger import SimpleActivityLedger
from web3_reverse_proxy.state.wrappers import (
    BasicBillingServiceWithLedger,
    SimpleAuthenticatorFromBilling,
)


class SampleStateManager:

    def __init__(
        self,
        billing: BasicBillingService,
        activity: SimpleActivityLedger,
        console_buffer: StringIO,
    ) -> None:
        self.billing_service = billing
        self.activity_ledger = activity

        self.admin_impl = RPCServiceAdmin(billing, activity, console_buffer)

        self.started_at = datetime.datetime.utcnow()

    def set_console_buffer(self, console_buffer: StringIO):
        self.admin_impl.set_console_buffer(console_buffer)

    def mark_next_startup(self) -> None:
        self.started_at = datetime.datetime.utcnow()

    def get_client_permissions_instance(self) -> ClientPermissions:
        return SimpleAuthenticatorFromBilling(self.billing_service)

    def get_call_permissions_instance(self) -> CallPermissions:
        user_summary_getter_fun = self.activity_ledger.get_all_time_user_summary
        return BasicBillingServiceWithLedger(
            self.billing_service, user_summary_getter_fun
        )

    def get_service_state_updater_instance(self) -> StateUpdater:
        return self.activity_ledger

    def get_admin_instance(self) -> RPCServiceAdmin:
        return self.admin_impl

    def register_proxy_stats(self, stats: RPCProxyStats) -> None:
        self.admin_impl.register_proxy_stats(stats)

    def register_endpoints(self, endpoints: Iterable[RPCEndpoint]) -> None:
        for e in endpoints:
            self.admin_impl.register_endpoint_stats(
                e.get_name(), e.get_connection_stats()
            )

    def clear_transient_fields(self):
        self.admin_impl.clear_transient_fields()

    def get_uptime(self, round_seconds: bool = True):
        dt = datetime.datetime.utcnow() - self.started_at

        if round_seconds:
            dt -= datetime.timedelta(microseconds=dt.microseconds)

        return dt
