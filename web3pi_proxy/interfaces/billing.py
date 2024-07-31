from typing import Protocol


class BillingPlanProtocol(Protocol):
    num_free_calls: int
    num_free_bytes: int
    glm_call_price: float
    glm_byte_price: float
    user_priority: int
    constant_pool: str | None
