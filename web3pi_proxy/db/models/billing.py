from peewee import IntegerField, FloatField, ForeignKeyField
from typing import Optional

from .__main__ import BaseModel
from .user import User


class BillingPlan(BaseModel):
    user: Optional[User] = ForeignKeyField(User)

    num_free_calls: int = IntegerField()
    num_free_bytes: int = IntegerField()
    glm_call_price: float = FloatField()
    glm_byte_price: float = FloatField()
    user_priority: int = IntegerField()

    class Meta:
        indexes = (
            (("user", ), True),
        )
