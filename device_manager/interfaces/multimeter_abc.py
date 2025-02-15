from abc import ABC, abstractmethod


class MultimeterABC(ABC):
    @abstractmethod
    def get_battery_mV(self) -> int:
        ...

    @abstractmethod
    def get_battery_mA(self) -> int:
        ...
