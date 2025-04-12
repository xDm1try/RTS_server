import asyncio
import gc
import json
import time
from machine import SPI
import aiohttp
import network
from device_manager.drivers.display.display_device import DisplayDevice
from device_manager.drivers.l298n import L298N_short
from device_manager.drivers.bq25895 import BQ25895, ChargerSettings, ChargerStatus
from device_manager.drivers.ina3221 import INA3221
from device_manager.drivers.temperature_sensors import TemperatureSensors
from server.models import HeartBeatResponse, TestData
from machine import Pin, SoftI2C, PWM
import ntptime
from onewire import OneWire


class DeviceSettings:

    def __init__(self,
                 server_ip: str,
                 server_port: int,
                 wifi_name: str,
                 wifi_passw: str,
                 device_name: str,
                 device_port: int, i2c_sda: int,
                 i2c_scl: int, charger_intr: int,
                 temp_pin: int,
                 temp_bat_addr: str,
                 temp_load_addr: str,
                 temp_env_addr: str,
                 broadcast_port: int,
                 pwm_pin: int,
                 display_spi: int,
                 display_DC: int,
                 display_RESET: int,
                 display_CS: int
                 ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.wifi_name = wifi_name
        self.wifi_passw = wifi_passw
        self.device_name = device_name
        self.device_port = device_port
        self.broadcast_port = broadcast_port
        self.i2c_sda = i2c_sda
        self.i2c_scl = i2c_scl
        self.charger_intr = charger_intr
        self.temp_pin = temp_pin
        self.temp_bat_addr = temp_bat_addr
        self.temp_load_addr = temp_load_addr
        self.temp_env_addr = temp_env_addr
        self.pwm_pin = pwm_pin
        self.display_spi = display_spi
        self.display_DC = display_DC
        self.display_RESET = display_RESET
        self.display_CS = display_CS


class TemperatureOf:
    BATTERY = "BAT"
    LOAD = "LOAD"
    ENVIRONMENT = "ENV"


class DeviceManager:
    SENSOR_LOOP = None

    BUSY = "device is busy"
    ERROR = "error happend"
    OK = "ok"

    STATUS = OK

    def __init__(self, ip, settings: DeviceSettings):
        assert settings, "No settings in DeviceController"
        self.dev_ip = ip
        
        self.settings: DeviceSettings = settings
        self.display_spi = SPI(settings.display_spi)

        self.i2c_bus = SoftI2C(scl=Pin(settings.i2c_scl), sda=Pin(settings.i2c_sda), freq=400000)
        self.onewire = OneWire(Pin(settings.temp_pin))
        self.pwm = PWM(Pin(self.settings.pwm_pin))
        self._init_display()

        # self.init_all_devices()
        
    def init_all_devices(self):

        self._init_charger()

        self._init_multimeter()

        self._init_temperature_sensors()

        self._init_load()

    def _init_load(self):
        self.load = L298N_short(self.pwm, 5000)

    def _init_temperature_sensors(self):
        addr_dict = [self.settings.temp_bat_addr, self.settings.temp_env_addr, self.settings.temp_load_addr]
        print(addr_dict)
        self.temp_sensors = TemperatureSensors(self.onewire, addr_dict)

    def _init_charger(self):
        self.charger: BQ25895 = BQ25895(self.i2c_bus, Pin(self.settings.charger_intr))

    def _init_multimeter(self):
        self.multimeter: INA3221 = INA3221(self.i2c_bus)

    def get_device_ip(self) -> str:
        return self.dev_ip

    def parameters_validation(self, test_data: TestData):
        settings: ChargerSettings = self.get_charging_settings()
        assert settings.const_current_mA < test_data.bat_current, "The current has reached the cut-off current"
        assert settings.const_volt_mV < test_data.bat_voltage * 1.15, "The voltage exceeds by 15 percent of entered"
        # assert test_data.temp_bat_limit < settings.temp_bat_limit, f"Battery overheating ({test_data.temp_bat})" TODO

    def _init_display(self):
        self.display: DisplayDevice = DisplayDevice(
            self.display_spi, self.settings.display_DC, self.settings.display_RESET, self.settings.display_CS)
        
    def _show_display(self):
        time_tuple: tuple = ntptime.gmtime()
        time_str: str = f"{}"
        self.display.show()
    
    async def acollect_parameters(self) -> TestData:
        voltage = self.get_battery_mV()
        current = self.get_battery_mA()
        duty = self.get_load_duty()
        status = self.get_charging_status()
        temp = self.temp_sensors.aread_temperature()
        test_data = TestData(
            temp_bat=temp[TemperatureOf.BATTERY],
            temp_env=temp[TemperatureOf.ENVIRONMENT],
            temp_load=temp[TemperatureOf.LOAD],
            bat_current=current,
            bat_voltage=voltage,
            load_duty=duty,
            charge_status=status
        )
        return test_data

    def collect_parameters(self) -> TestData:
        voltage = self.get_battery_mV()
        current = self.get_battery_mA()
        duty = self.get_load_duty()
        status = self.get_charging_status()
        temp = self.temp_sensors.read_temperature()
        test_data = TestData(
            temp_bat=temp[TemperatureOf.BATTERY],
            temp_env=temp[TemperatureOf.ENVIRONMENT],
            temp_load=temp[TemperatureOf.LOAD],
            bat_current=current,
            bat_voltage=voltage,
            load_duty=duty,
            charge_status=status
        )
        return test_data

    async def acollect_parameters_json(self) -> str:
        test_data = await self.acollect_parameters()
        try:
            self.parameters_validation(test_data=test_data)
        except AssertionError as e:
            print(e)
            self.reset_all()
        return json.dumps(test_data)
    
    def collect_parameters_json(self) -> str:
        test_data = self.collect_parameters()
        try:
            self.parameters_validation(test_data=test_data)
        except AssertionError as e:
            print(e)
            self.reset_all()
        return json.dumps(test_data)

    def get_battery_mV(self) -> int:
        return self.multimeter.get_battery_mV()

    def get_battery_mA(self) -> int:
        return self.multimeter.get_battery_mA()

    def get_load_duty(self) -> int:
        return self.load.get_duty()

    def set_load_duty(self, duty: int) -> None:
        return self.load.set_duty(duty)

    def start_charging(self, settings: ChargerSettings):
        self.charger.start_charging(settings)

    def stop_charging(self):
        self.charger.set_charge_enable(False)

    def get_charging_settings(self) -> ChargerSettings:
        return BQ25895.charge_settings

    def get_charging_status(self) -> ChargerStatus:
        return self.charger.get_charger_status()

    def reset_charger(self) -> None:
        self.charger.reset()

    def reset_all(self) -> None:
        self.charger.reset()
        self.load.set_duty(0)

    def get_status(self) -> HeartBeatResponse:
        status = self.STATUS
        name = self.settings.device_name
        ip = self.get_device_ip()
        ch_status = self.get_charging_status()

        resp = HeartBeatResponse(device_status=status, device_name=name, device_ip=ip, charger_status=ch_status)
        return resp
