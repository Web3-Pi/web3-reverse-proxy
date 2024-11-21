from peewee import CharField, TextField

from .__main__ import BaseModel


class Endpoint(BaseModel):
    name: str = CharField()

    config: str = TextField()

    class Meta:
        indexes = (
            (("name", ), True),
        )
