from peewee import IntegerField, FloatField

from .__main__ import BaseModel


class BillingPlan(BaseModel):
    num_free_calls: int = IntegerField()
    num_free_bytes: int = IntegerField()
    glm_call_price: float = FloatField()
    glm_byte_price: float = FloatField()
    user_priority: int = IntegerField()
