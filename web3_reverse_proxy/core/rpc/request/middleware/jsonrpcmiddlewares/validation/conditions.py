import re
from abc import ABC, abstractmethod
from typing import Any, List


class Condition(ABC):
    def validate(self, value: Any) -> bool:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class In(Condition):
    def __init__(self, *values) -> None:
        self.values = values

    def validate(self, value: Any) -> bool:
        return value in self.values

    @property
    def description(self) -> str:
        return f"is {', '.join([str(item) for item in self.values[:-1]])} or {self.values[-1]}"


class Exact(Condition):
    def __init__(self, value: Any) -> None:
        self.value = value

    def validate(self, value: Any) -> bool:
        return value == self.value

    @property
    def description(self) -> str:
        return f"is {self.value}"


class Matches(Condition):
    def __init__(self, regex: str) -> None:
        self.regex = regex

    def validate(self, value: Any) -> bool:
        return bool(re.match(self.regex, str(value)))

    @property
    def description(self) -> str:
        return f"matches regex {self.regex}"


class ConditionWrapper(Condition, ABC):
    def __init__(self, condition: Condition) -> None:
        self.condition = condition


class Type(ConditionWrapper):
    def validate(self, value: Any) -> bool:
        return self.condition.validate(type(value))

    @property
    def description(self) -> str:
        return f"type {self.condition.description}"
