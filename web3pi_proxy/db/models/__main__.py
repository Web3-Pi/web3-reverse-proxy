from peewee import Model
from playhouse.shortcuts import model_to_dict, dict_to_model
from typing import Any, Dict

from ..__main__ import db


class BaseModel(Model):
    class Meta:
        database = db

    def __str__(self):
        return f"{self.to_dict()}"

    def to_dict(self):
        return model_to_dict(self, extra_attrs=getattr(self.__class__._meta, "extra_attrs", list()))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return dict_to_model(cls, data)
