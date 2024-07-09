from peewee import Model

from ..__main__ import db


class BaseModel(Model):
    class Meta:
        database = db
