from .__main__ import BaseModel

from peewee import IntegerField, FloatField


class BillingPlan(BaseModel):
    num_free_calls = IntegerField()
    num_free_bytes = IntegerField()
    glm_call_price = FloatField()
    glm_byte_price = FloatField()
    user_priority = IntegerField()
