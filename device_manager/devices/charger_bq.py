from machine import I2C
from machine import Pin
from device_Controller.drivers.bq25895 import BQ25895
from device_Controller.interfaces.charger_abc import ChargerABC
from device_Controller.interfaces.charger_abc import ChargerStatus
from device_Controller.interfaces.charger_abc import ChargerSettings


class ChargerBQ(ChargerABC):

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
            self.apply_settings(ChargerSettings())
        except Exception as e:
            print("Didn't reset charger")
            raise e

    def apply_settings(self, settings: ChargerSettings) -> None:
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
        self.apply_settings(settings=settings)
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
