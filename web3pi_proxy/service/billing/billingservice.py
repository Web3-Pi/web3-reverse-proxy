from typing import Dict, Generic, List, Type, TypeVar

from web3pi_proxy.interfaces.billing import BillingPlanProtocol

BPP = TypeVar("BPP", bound=BillingPlanProtocol)


class BasicBillingService(Generic[BPP]):
    billing_plan_type: Type[BPP]
    user_plans: Dict[str, BPP]

    def __init__(self, billing_plan_type: Type[BPP]):
        self.billing_plan_type = billing_plan_type
        self.users_plans = dict()

    def is_registered(self, user_api_key: str) -> bool:
        return user_api_key in self.users_plans

    def register_user(
        self, user_api_key: str, billing_plan: BPP
    ) -> None:
        assert user_api_key not in self.users_plans

        self.users_plans[user_api_key] = billing_plan

    def remove_user(self, user_api_key: str) -> None:
        if self.is_registered(user_api_key):
            del self.users_plans[user_api_key]

    def update_user_plan(
        self, user_api_key: str, billing_plan: BPP
    ) -> None:
        assert self.is_registered(user_api_key)

        self.users_plans[user_api_key] = billing_plan

    def get_registered_users_api_keys(self) -> List[str]:
        return list(self.users_plans.keys())

    def get_user_plan(self, user_api_key: str) -> BPP:
        res = None
        if self.is_registered(user_api_key):
            res = self.users_plans[user_api_key]

        return res

    # FIXME: GLM settlements should also be verified here (although they should be read only when necessary,
    #  and definitely not every time rpc call is invoked by user
    def is_allowed(
        self,
        user_api_key: str,
        method: str,
        num_calls_so_far: int,
        num_bytes_so_far: int,
    ) -> bool:
        if not self.is_registered(user_api_key):
            return False

        assert method is not None
        plan = self.users_plans[user_api_key]

        return (
            plan.num_free_calls > num_calls_so_far
            and plan.num_free_bytes > num_bytes_so_far
        )

    def get_call_priority(self, user_api_key: str, method: str) -> int:
        assert self.is_registered(user_api_key)
        assert method is not None

        return self.users_plans[user_api_key].user_priority

    def create_plan(
        self, free_calls: int | str, free_bytes: int | str, priority: int | str
    ) -> BPP:
        # FIXME: naive type handling
        free_calls_num = int(free_calls)
        free_bytes_num = int(free_bytes)
        priority = int(priority)

        return self.billing_plan_type(free_calls_num, free_bytes_num, 0.0, 0.0, priority)
