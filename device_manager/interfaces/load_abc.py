from abc import ABC, abstractmethod


class LoadABC(ABC):

    @abstractmethod
    def set_resistance(self, percentage: int):
        ...

    @abstractmethod
    def get_resistance(self) -> int:
        ...
