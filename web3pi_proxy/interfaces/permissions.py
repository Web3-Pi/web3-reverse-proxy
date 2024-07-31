from abc import ABC, abstractmethod


class ClientPermissions(ABC):

    @abstractmethod
    def is_authorized(self, user_api_key: str) -> bool:
        pass


class CallPermissions(ABC):

    @abstractmethod
    def is_allowed(self, user_api_key: str, method: str) -> bool:
        pass

    @abstractmethod
    def get_call_priority(self, user_api_key: str, method: str) -> int:
        pass

    def get_user_constant_pool(self, user_api_key: str) -> str | None:
        pass
