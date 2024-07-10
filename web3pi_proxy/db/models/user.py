from peewee import CharField

from .__main__ import BaseModel


class User(BaseModel):
    api_key: str = CharField()

    class Meta:
        indexes = (
            (("api_key", ), True),
        )
