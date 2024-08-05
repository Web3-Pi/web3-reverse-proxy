from __future__ import annotations


class SimplestBillingPlan:
    num_free_calls: int
    num_free_bytes: int
    glm_call_price: float
    glm_byte_price: float
    user_priority: int
    constant_pool: str | None

    NUM_FREE_CALLS = "num_free_calls"
    NUM_FREE_BYTES = "num_free_bytes"
    GLM_CALL_PRICE = "glm_call_price"
    GLM_BYTE_PRICE = "glm_byte_price"
    USER_PRIORITY = "user_priority"
    CONSTANT_POOL = "constant_pool"

    def __init__(
        self,
        num_free_calls: int,
        num_free_bytes: int,
        glm_call_price: float,
        glm_byte_price: float,
        user_priority: int,
        constant_pool: str | None,
    ) -> None:
        self.num_free_calls = num_free_calls
        self.num_free_bytes = num_free_bytes
        self.glm_call_price = glm_call_price
        self.glm_byte_price = glm_byte_price
        self.user_priority = user_priority
        self.constant_pool = constant_pool

    def to_dict(self) -> dict:
        return {
            self.NUM_FREE_CALLS: self.num_free_calls,
            self.NUM_FREE_BYTES: self.num_free_bytes,
            self.GLM_CALL_PRICE: self.glm_call_price,
            self.GLM_BYTE_PRICE: self.glm_byte_price,
            self.USER_PRIORITY: self.user_priority,
            self.CONSTANT_POOL: self.constant_pool,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SimplestBillingPlan:
        assert len(dict) == 2
        assert cls.NUM_FREE_BYTES in d
        assert cls.NUM_FREE_CALLS in d
        assert cls.USER_PRIORITY in d

        return SimplestBillingPlan(
            d[cls.NUM_FREE_CALLS], d[cls.NUM_FREE_BYTES], 0.0, 0.0, d[cls.USER_PRIORITY], d.get(cls.CONSTANT_POOL)
        )
