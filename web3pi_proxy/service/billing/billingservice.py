from typing import Dict, Generic, List, Type, TypeVar

from web3pi_proxy.interfaces.billing import BillingPlanProtocol

BPP = TypeVar("BPP", bound=BillingPlanProtocol)


class BasicBillingService(Generic[BPP]):
    billing_plan_type: Type[BPP]
    user_plans: Dict[str, BPP]

    def __init__(self, billing_plan_type: Type[BPP]):
        self.billing_plan_type = billing_plan_type
        self.user_plans = dict()

    def is_registered(self, user_api_key: str) -> bool:
        return user_api_key in self.user_plans

    def register_user(
        self, user_api_key: str, billing_plan: BPP
    ) -> None:
        self.user_plans.setdefault(user_api_key, billing_plan)

    def remove_user(self, user_api_key: str) -> None:
        self.user_plans.pop(user_api_key, None)

    def update_user_plan(
        self, user_api_key: str, new_billing_plan: BPP
    ) -> None:
        assert self.is_registered(user_api_key)
        billing_plan = self.user_plans[user_api_key]
        for attr in BillingPlanProtocol.__annotations__.keys():
            setattr(billing_plan, attr, getattr(new_billing_plan, attr))

    def get_registered_users_api_keys(self) -> List[str]:
        return list(self.user_plans.keys())

    def get_user_plan(self, user_api_key: str) -> BPP:
        return self.user_plans.get(user_api_key, None)

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
        plan = self.user_plans[user_api_key]

        return (
            plan.num_free_calls > num_calls_so_far
            and plan.num_free_bytes > num_bytes_so_far
        )

    def get_call_priority(self, user_api_key: str, method: str) -> int:
        assert self.is_registered(user_api_key)
        assert method is not None

        return self.user_plans[user_api_key].user_priority

    def get_user_constant_pool(self, user_api_key: str) -> str | None:
        assert self.is_registered(user_api_key)

        return self.user_plans[user_api_key].constant_pool

    def create_plan(
        self, free_calls: int | str, free_bytes: int | str, priority: int | str, constant_pool: str | None
    ) -> BPP:
        # FIXME: naive type handling
        return self.billing_plan_type(
            num_free_calls=int(free_calls),
            num_free_bytes=int(free_bytes),
            glm_call_price=0.0,
            glm_byte_price=0.0,
            user_priority=int(priority),
            constant_pool=constant_pool
        )
