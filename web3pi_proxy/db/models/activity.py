import datetime
from peewee import CharField, ForeignKeyField, IntegerField, DateField
from playhouse.hybrid import hybrid_property

from .__main__ import BaseModel
from .user import User


class CallStats(BaseModel):
    user: User = ForeignKeyField(User)  # None - total system stats
    method: str = CharField()  # None - activity summary
    date: datetime.date = DateField()  # None - all time summary

    request_bytes: int = IntegerField(default=0)
    response_bytes: int = IntegerField(default=0)
    num_calls: int = IntegerField(default=0)

    class Meta:
        indexes = (
            (("user", "method", "date"), True),
        )
        extra_attrs = ["total_bytes"]

    @hybrid_property
    def total_bytes(self) -> int:
        return self.request_bytes + self.response_bytes

    def update_stats(self, request_bytes: int, response_bytes: int, num_calls: int) -> None:
        self.request_bytes += request_bytes
        self.response_bytes += response_bytes
        self.num_calls += num_calls
