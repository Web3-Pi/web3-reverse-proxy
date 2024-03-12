from abc import ABC
from typing import Any, List
import re


class Condition(ABC):
    def validate(self, value: Any) -> bool:
        pass


class In(Condition):
    def __init__(self, *values) -> None:
        self.values = values

    def validate(self, value: Any) -> bool:
        return value in self.values


class Exact(Condition):
    def __init__(self, value: Any) -> None:
        self.value = value

    def validate(self, value: Any) -> bool:
        return value == self.value


class Matches(Condition):
    def __init__(self, regex: str) -> None:
        self.regex = regex

    def validate(self, value: Any) -> bool:
        return bool(re.match(self.regex, str(value)))


class Operator(Condition, ABC):
    def __init__(self, *conditions: List[Condition]) -> None:
        self.conditions = conditions


class And(Operator):
    def validate(self, value: Any) -> bool:
        for condition in self.conditions:
            if not condition.validate(value):
                return False
        return True


class Or(Operator):
    def validate(self, value: Any) -> bool:
        for condition in self.conditions:
            if condition.validate(value):
                return True
        return False


class ConditionWrapper(Condition, ABC):
    def __init__(self, condition: Condition) -> None:
        self.condition = condition


class Type(ConditionWrapper):
    def validate(self, value: Any) -> bool:
        return self.condition.validate(type(value))
