from abc import ABC, abstractmethod


class ChargerSettings:
    def __init__(self,
                 const_current_mA: int = 130,
                 const_volt_mV: int = 4200,
                 cut_off_current_mA: int = 20
                 ):
        self.const_current_mA: int = const_current_mA
        self.const_volt_mV: int = const_volt_mV
        self.cut_off_current_mA: int = cut_off_current_mA

    def __repr__(self) -> str:
        return (
            f"ChargerSettings:"
            f"const_current_mA={self.const_current_mA!r}\n"
            f"const_volt_mV={self.const_volt_mV!r}\n"
            f"cut_off_current_mA={self.cut_off_current_mA!r}\n"
        )

class ChargerStatus:
    def __init__(self,
                 const_current_mA: int,
                 const_volt_mV: int,
                 cut_off_current_mA: int,
                 input_type: str,
                 charge_status: str,
                 adc_battery_mV: int,
                 adc_bus_mV: int,
                 adc_current: int,
                 batfet_mode: bool,
                 termination_enabled: bool,
                 precharge_current: int,
                 low_battery_mV: int,
                 ):
        self.const_current_mA = const_current_mA
        self.const_volt_mV = const_volt_mV
        self.cut_off_current_mA = cut_off_current_mA
        self.input_type = input_type
        self.charge_status = charge_status
        self.adc_battery_mV = adc_battery_mV
        self.adc_bus_mV = adc_bus_mV
        self.adc_current = adc_current
        self.batfet_mode = batfet_mode
        self.termination_enabled = termination_enabled
        self.precharge_current = precharge_current
        self.low_battery_mV = low_battery_mV

    def __repr__(self) -> str:
        return (
            f"ChargerStatus:"
            f"const_current_mA={self.const_current_mA!r}\n"
            f"const_volt_mV={self.const_volt_mV!r}\n"
            f"cut_off_current_mA={self.cut_off_current_mA!r}\n"
            f"input_type={self.input_type!r}\n"
            f"charge_status={self.charge_status!r}\n"
            f"adc_battery_mV={self.adc_battery_mV!r}\n"
            f"adc_bus_mV={self.adc_bus_mV!r}\n"
            f"adc_current={self.adc_current!r}\n"
            f"batfet_mode={self.batfet_mode!r}\n"
            f"termination_enabled={self.termination_enabled!r}\n"
            f"precharge_current={self.precharge_current!r}\n"
            f"low_battery_mV={self.low_battery_mV!r})\n"
        )


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
