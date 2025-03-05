from machine import I2C
from machine import Pin
from device_manager.drivers.bq25895 import BQ25895


class ChargerSettings:
    def __init__(self,
                 const_current_mA: int = 130,
                 const_volt_mV: int = 4200,
                 cut_off_current_mA: int = 20,
                 temp_bat_limit: int = 50,
                 ):
        self.const_current_mA: int = const_current_mA
        self.const_volt_mV: int = const_volt_mV
        self.cut_off_current_mA: int = cut_off_current_mA
        self.temp_bat_limit: int = temp_bat_limit

    def __repr__(self) -> str:
        return (
            f"ChargerSettings:"
            f"const_current_mA={self.const_current_mA!r}\n"
            f"const_volt_mV={self.const_volt_mV!r}\n"
            f"cut_off_current_mA={self.cut_off_current_mA!r}\n"
            f"temp_bat_limit={self.temp_bat_limit!r}\n"
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


class ChargerBQ:

    def __init__(self, i2c: I2C, int_pin: Pin, handler=None):
        self.i2c = i2c
        self.int_pin = int_pin
        self._handler = handler
        self.charger_settings: ChargerSettings = ChargerSettings()
        if BQ25895.is_enabled(self.i2c):
            self.bq: BQ25895 = BQ25895(self.i2c, self.int_pin, self._handler)
            self.bq.reset()
        else:
            raise Exception("Charger not detected")

    def reset(self):
        try:
            self.bq.reset()
            self._apply_settings(ChargerSettings())
            self.terminate_charging()
        except Exception as e:
            print("Didn't reset charger")
            raise e

    def _apply_settings(self, settings: ChargerSettings) -> None:
        self.charger_settings = settings
        const_current_mA: int = settings.const_current_mA
        const_volt_mV: int = settings.const_volt_mV
        cut_off_current_mA: int = settings.cut_off_current_mA

        try:
            self.bq.set_charge_current(const_current_mA)
            self.bq.set_current_cut_off(cut_off_current_mA)
            self.bq.set_charge_voltage(const_volt_mV)
        except Exception as e:
            print("Didn't apply charger")
            raise e

    def start_charging(self, settings: ChargerSettings) -> None:
        self._apply_settings(settings=settings)
        self.bq.set_charge_enable(True)

    def terminate_charging(self) -> None:
        self.bq.set_charge_enable(False)

    def get_charger_status(self) -> ChargerStatus:
        status = ChargerStatus(
            self.bq.get_charge_current(),
            self.bq.get_charge_voltage(),
            self.charger_settings.cut_off_current_mA,
            self.bq.get_input_type_str(),
            self.bq.get_charge_state(),
            self.bq.adc_battery_volt(),
            self.bq.adc_vbus_volt(),
            self.bq.adc_charge_current(),
            self.bq.get_batfet_mode(),
            self.bq.get_charging_termination(),
            self.bq.get_current_precharge_limit(),
            self.bq.get_precharge_threshold()
        )
        return status

    def get_charger_settings(self) -> ChargerSettings:
        return self.charger_settings
