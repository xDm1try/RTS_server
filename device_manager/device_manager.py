from device_manager.drivers.l298n import L298N_short
from device_manager.drivers.bq25895 import BQ25895, ChargerSettings, ChargerStatus
from device_manager.drivers.ina3221 import INA3221
from device_manager.drivers.temperature_sensors import TemperatureSensors
from models import HeartBeatResponse
from machine import Pin, I2C, PWM
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
                 pwm_pin: int):
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

    def __init__(self, device_ip, settings: DeviceSettings):
        assert settings, "No settings in DeviceController"
        self.settings: DeviceSettings = settings
        self.dev_ip = device_ip
        self.i2c_bus = I2C(scl=Pin(settings.i2c_scl), sda=Pin(settings.i2c_sda), freq=400000)
        self.onewire = OneWire(Pin(settings.temp_pin))
        self.pwm = Pin(self.settings.pwm_pin)

        # self.init_all_devices()

    def init_all_devices(self):

        self._init_charger()

        self._init_multimeter()

        self._init_temperature_sensors()

        self._init_load()

    def _init_load(self):
        self.load = L298N_short(self.pwm)

    def _init_temperature_sensors(self):
        self.temp_sensors = TemperatureSensors()

    def _init_charger(self):
        self.charger: BQ25895 = BQ25895(self.i2c, Pin(self.settings.charger_intr))

    def _init_multimeter(self):
        self.multimeter: INA3221 = INA3221(self.i2c_bus)

    def get_device_ip(self) -> str:
        return self.dev_ip

    async def get_temperatures(self) -> dict[str, float]:
        d = await self.temp_sensors.read_temperature()
        d[TemperatureOf.BATTERY] = d[self.settings.temp_bat_addr]
        d[TemperatureOf.ENVIRONMENT] = d[self.settings.temp_env_addr]
        d[TemperatureOf.LOAD] = d[self.settings.temp_load_addr]
        return d

    async def get_battery_mV(self) -> int:
        return self.multimeter.get_battery_mV()

    async def get_battery_mA(self) -> int:
        return self.multimeter.get_battery_mA()

    async def get_load_duty(self) -> int:
        return self.load.get_duty()

    async def set_load_duty(self, duty: int) -> None:
        return self.load.set_duty(duty)

    async def start_charging(self, settings: ChargerSettings):
        self.charger.start_charging(settings)

    async def stop_charging(self):
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

    async def get_status(self) -> HeartBeatResponse:
        status = self.STATUS
        name = self.settings.device_name
        ip = self.get_device_ip()
        ch_status = self.get_charging_status()

        resp = HeartBeatResponse(device_status=status, device_name=name, device_ip=ip, charger_status=ch_status)
        return resp
