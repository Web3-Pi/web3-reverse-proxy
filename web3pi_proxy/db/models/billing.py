from peewee import IntegerField, FloatField, ForeignKeyField, CharField
from typing import Optional

from .__main__ import BaseModel
from .user import User


class BillingPlan(BaseModel):
    user: Optional[User] = ForeignKeyField(User)

    num_free_calls: int = IntegerField(default=0)
    num_free_bytes: int = IntegerField(default=0)
    glm_call_price: float = FloatField(default=0.0)
    glm_byte_price: float = FloatField(default=0.0)
    user_priority: int = IntegerField(default=0)
    constant_pool: str | None = CharField(null=True)

    class Meta:
        indexes = (
            (("user", ), True),
        )
