from abc import ABC, abstractmethod


class StateUpdater(ABC):

    @abstractmethod
    def record_processed_rpc_call(self, request, response) -> None:
        pass
