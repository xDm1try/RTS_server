from abc import ABC, abstractmethod




class ChargerABC(ABC):

    @abstractmethod
    def reset(self):
        ...

    @abstractmethod
    def apply_settings(self, settings: ChargerSettings) -> None:
        ...

    @abstractmethod
    def start_charging(self, settings: ChargerSettings) -> None:
        ...

    @abstractmethod
    def terminate_charging(self) -> None:
        ...

    @abstractmethod
    def get_charger_status(self) -> ChargerStatus:
        ...

    @abstractmethod
    def get_charger_settings(self) -> ChargerSettings:
        ...
