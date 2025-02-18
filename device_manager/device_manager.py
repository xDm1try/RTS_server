from device_manager.network_controller.connection_controller import ConnectionController
from device_manager.devices.charger_bq import ChargerBQ
from device_manager.devices.load_l298n import LoadL298N
from device_manager.devices.multimeter import MultimeterINA3221
from device_manager.devices.temperature_sensors import TemperatureSensors
from machine import Pin, I2C, OneWire, PWM


class DeviceSettings:

    def __init__(self, device_name: str,
                 device_port: int, i2c_sda: int,
                 i2c_scl: int, charger_intr: int,
                 temp_pin: int,
                 temp_bat_addr,
                 temp_load_addr,
                 temp_env_addr,
                 pwm_pin: int):
        self.device_name = device_name
        self.device_port = device_port
        self.i2c_sda = i2c_sda
        self.i2c_scl = i2c_scl
        self.charger_intr = charger_intr
        self.temp_pin = temp_pin
        self.temp_bat_addr = temp_bat_addr
        self.temp_load_addr = temp_load_addr
        self.temp_env_addr = temp_env_addr
        self.pwm_pin = pwm_pin


class DeviceController:

    def __init__(self, settings: DeviceSettings = None):
        assert settings, "No settings in DeviceController"
        self.settings = settings

        self.start_controllers(self.settings)

    def start_controllers(self, settings: DeviceSettings):
        self.connection_c = ConnectionController(settings.device_name)
        self.connection_c.run_udp_handler(settings.device_port)

        self.i2c_bus = I2C(scl=Pin(settings.i2c_scl), sda=Pin(settings.i2c_sda), freq=400000)
        self.charger = ChargerBQ(self.i2c_bus, Pin(settings.charger_intr))

        self.multimeter = MultimeterINA3221(self.i2c_bus)

        self.onewire = OneWire(Pin(settings.temp_pin))
        self.temp_sensors = TemperatureSensors()

        self.load = LoadL298N(Pin(settings.pwm_pin))

    def stop_controllers(self):
        self.connection_c.stop_udp_handler()

    def get_temperature(self):
        ...
