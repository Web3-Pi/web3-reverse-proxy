import time
from abc import ABC
from dataclasses import dataclass
from typing import Any, Type


@dataclass
class CacheRecord:
    value: Any


@dataclass
class ExpirableCacheRecord(CacheRecord):
    expiry: int


class Cache:
    def __init__(self, cache_record_class: Type[CacheRecord] = CacheRecord) -> None:
        self._memory = {}
        self.record_class = cache_record_class

    def add(self, key: str, value: Any, *args, **kwargs) -> None:
        self._memory[key] = self.record_class(value, *args, **kwargs)

    def get(self, key: str) -> CacheRecord | None:
        return self._memory.get(key)

    def remove(self, key: str) -> None:
        if self._memory.get(key):
            del self._memory[key]


class CacheService(ABC):
    def __init__(self, cache_record_class: Type[CacheRecord] = CacheRecord) -> None:
        self._cache = Cache(cache_record_class)

    def _is_record_valid(self, record: CacheRecord) -> bool:
        pass

    def store(self, key: str, value: Any) -> None:
        pass

    def get(self, key: str) -> Any:
        cache_record = self._cache.get(key)
        if cache_record is None or not self._is_record_valid(cache_record):
            self._cache.remove(key)
            return None
        return cache_record.value


class ExpirableCacheService(CacheService):
    def __init__(
        self,
        expiry_milis: int,
        cache_record_class: Type[ExpirableCacheRecord] = ExpirableCacheRecord,
    ) -> None:
        super().__init__(cache_record_class)
        self._expiry_ns = expiry_milis * 10**6

    def _is_record_valid(self, record: ExpirableCacheRecord):
        return record.expiry > time.time_ns()

    def store(self, key: str, value: Any) -> None:
        self._cache.add(key, value, time.time_ns() + self._expiry_ns)
