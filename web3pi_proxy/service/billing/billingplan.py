from __future__ import annotations


class SimplestBillingPlan:

    NUM_FREE_CALLS = "num_free_calls"
    NUM_FREE_BYTES = "num_free_bytes"
    GLM_CALL_PRICE = "glm_call_price"
    GLM_BYTE_PRICE = "glm_byte_price"
    USER_PRIORITY = "user_priority"

    def __init__(
        self,
        no_free_calls: int,
        no_free_bytes: int,
        glm_call_price: float,
        glm_byte_price: float,
        user_priority: int,
    ) -> None:
        self.no_free_calls = no_free_calls
        self.no_free_bytes = no_free_bytes
        self.glm_call_price = glm_call_price
        self.glm_byte_price = glm_byte_price
        self.user_priority = user_priority

    def to_dict(self) -> dict:
        return {
            self.NUM_FREE_CALLS: self.no_free_calls,
            self.NUM_FREE_BYTES: self.no_free_bytes,
            self.GLM_CALL_PRICE: self.glm_call_price,
            self.GLM_BYTE_PRICE: self.glm_byte_price,
            self.USER_PRIORITY: self.user_priority,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SimplestBillingPlan:
        assert len(dict) == 2
        assert cls.NUM_FREE_BYTES in d
        assert cls.NUM_FREE_CALLS in d
        assert cls.USER_PRIORITY in d

        return SimplestBillingPlan(
            d[cls.NUM_FREE_CALLS], d[cls.NUM_FREE_BYTES], 0.0, 0.0, d[cls.USER_PRIORITY]
        )
