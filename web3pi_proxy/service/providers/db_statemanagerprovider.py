from io import StringIO

from web3pi_proxy.db.models import BillingPlan, CallStats, User

from web3pi_proxy.service.billing.billingservice import BasicBillingService
from web3pi_proxy.service.ledger.activityledger import SimpleActivityLedger
from web3pi_proxy.service.ledger.activitysummary import ServiceActivitySummary, UserActivitySummary
from web3pi_proxy.state.statemanager import SampleStateManager


class DbStateManagerProvider:

    @classmethod
    def create_state_manager(
        cls,
        console_buffer: StringIO,
    ) -> SampleStateManager:
        billing_service = BasicBillingService(BillingPlan)
        activity = SimpleActivityLedger()

        cls._populate_billing_service(billing_service)
        cls._populate_activity_ledger(activity)

        state_manager = SampleStateManager(
            billing_service, activity, console_buffer
        )

        return state_manager

    @classmethod
    def close_state_manager(
        cls,
        ssm: SampleStateManager,
    ) -> None:
        cls._save_billing_service(ssm.billing_service)
        cls._save_activity_ledger(ssm.activity_ledger)
        print(f"Service uptime for this session: {ssm.get_uptime()}")

    @classmethod
    def _save_billing_service(cls, billing_service: BasicBillingService[BillingPlan]):
        for api_key, bp in billing_service.user_plans.items():
            bp.user, _ = User.get_or_create(api_key=api_key)
            bp.save()

    @classmethod
    def _populate_billing_service(cls, billing_service: BasicBillingService[BillingPlan]):
        for bp in BillingPlan.select():
            billing_service.register_user(bp.user.api_key, bp)

    @classmethod
    def _save_activity_ledger(cls, activity: SimpleActivityLedger):
        for date_key, date_summary in activity.daily_usage.items():
            for api_key, user_summary in date_summary.user_summaries.items():
                for method, mem_cs in user_summary.method_stats.items():
                    user, _ = User.get_or_create(api_key=api_key)
                    cs, _ = CallStats.get_or_create(user=user, date=date_key, method=method)
                    cs.request_bytes = mem_cs.request_bytes
                    cs.response_bytes = mem_cs.response_bytes
                    cs.num_calls = mem_cs.num_calls
                    cs.save()

    @classmethod
    def _populate_activity_ledger(cls, activity: SimpleActivityLedger):
        for cs in CallStats.select():
            api_key = cs.user.api_key
            date_key = cs.date.strftime("%Y-%m-%d")
            total_user_summary = activity.all_time_summary.user_summaries.setdefault(
                api_key,
                UserActivitySummary(cs.user)
            )

            date_summary = activity.daily_usage.setdefault(date_key, ServiceActivitySummary())
            date_user_summary = date_summary.user_summaries.setdefault(
                api_key,
                UserActivitySummary(cs.user)
            )

            total_user_summary.update(cs.method, cs.request_bytes, cs.response_bytes, cs.num_calls)
            date_user_summary.update(cs.method, cs.request_bytes, cs.response_bytes, cs.num_calls)
