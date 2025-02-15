from machine import I2C, PIN
from device_manager.interfaces.multimeter_abc import MultimeterABC
from device_manager.drivers.ina3221 import INA3221


class MultimeterINA3221(MultimeterABC):
    def __init__(self, i2c: I2C, channel: int = 1):
        self.channel = channel
        self.ina3221 = INA3221(i2c)
        self.ina3221.enable_channel(self.channel)

    def get_battery_mV(self) -> int:
        self.ina3221.bus_voltage(self.channel) * 1000

    def get_battery_mA(self) -> int:
        self.ina3221.current(self.channel) * 1000
