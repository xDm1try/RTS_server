import asyncio
import gc
import os
from device_manager.drivers.display.display_device import DisplayDevice
from device_manager.drivers.l298n import L298N_short
from device_manager.drivers.bq25895 import BQ25895, ChargerSettings, ChargerStatus
from device_manager.drivers.ina3221 import INA3221
from device_manager.drivers.sdcard import SDCard
from device_manager.drivers.temperature_sensors import TemperatureSensors
# import os
# from device_manager.drivers.sdcard import SDCard
from server.models import HeartBeatResponse, TestData
from ntptime import gmtime
from machine import Pin, SoftI2C, PWM, SPI
from onewire import OneWire
from json import dumps
import time


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
                 display_CS: int,
                 sdcard_SPI: int,
                 sdcard_CS: int
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
        self.sdcard_SPI = sdcard_SPI
        self.sdcard_CS = sdcard_CS


class TemperatureOf:
    BATTERY = "BAT"
    LOAD = "LOAD"
    ENVIRONMENT = "ENV"


class DeviceManager:
    SENSOR_LOOP = None
    SENSOR_LOOP_STARTED = asyncio.Event()
    CURRENT_HOLDER_STARTED = asyncio.Event()
    HELD_CURRENT = None
    FILE_NAME = "test_data.txt"

    BUSY = "device is busy"
    ERROR = "error happend"
    OK = "ok"

    STATUS = OK

    PARAMETERS_LOCK = asyncio.Lock()

    def __init__(self, ip, settings: DeviceSettings):
        assert settings, "No settings in DeviceController"
        self.dev_ip = ip

        self.settings: DeviceSettings = settings
        self.display_spi = SPI(settings.display_spi, baudrate=60000000)
        
        self.SD_PATH = "/sd"
        print(gc.mem_free())
        sd = SDCard(SPI(settings.sdcard_SPI), Pin(settings.sdcard_CS))
        os.mount(sd, self.SD_PATH)
        assert "sd" in os.listdir("/"), "No sdcard mounted directory"

        self.i2c_bus = SoftI2C(scl=Pin(settings.i2c_scl), sda=Pin(settings.i2c_sda), freq=400000)
        self.onewire = OneWire(Pin(settings.temp_pin))
        self.pwm = PWM(Pin(self.settings.pwm_pin))

        self.init_all_devices()

    def init_all_devices(self):

        self._init_charger()

        self._init_multimeter()

        self._init_temperature_sensors()

        self._init_load()

        self._init_display()

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

    def _init_display(self):
        self.display: DisplayDevice = DisplayDevice(
            self.display_spi, self.settings.display_DC, self.settings.display_RESET, self.settings.display_CS)
        self._show_display()

    def _show_display(self, parameters: TestData | None = None):
        time_tuple: tuple = gmtime()
        time_str: str = f"{time_tuple[3]:02d}:{time_tuple[4]:02d}:{time_tuple[5]:02d}"
        params = parameters if parameters is not None else self.collect_parameters()
        charger_input = self.charger.get_input_type_str()

        self.display.show(time_value=time_str, device_name=self.settings.device_name, chg_status=params.charge_status,
                          v_bat=params.bat_voltage, current_bat=params.bat_current, temp_bat=params.temp_bat,
                          temp_env=params.temp_env, temp_load=params.temp_load, load_duty=params.load_duty,
                          ip=self.dev_ip, load_voltage=params.load_voltage,
                          load_current=params.load_current, input_status=charger_input,
                          const_current=params.const_current, const_volt=params.const_voltage)

    async def acollect_parameters(self) -> TestData:
        await asyncio.sleep(1)
        bat_voltage = self.multimeter.get_battery_mV()
        bat_current = self.multimeter.get_battery_mA()
        load_current = self.multimeter.get_load_mA()
        load_voltage = self.multimeter.get_load_mV()
        cc = self.charger.get_charge_current() if "Pre-" not in self.charger.get_charge_state() \
            else self.charger.get_current_precharge_limit()
        cv = self.charger.get_charge_voltage() if "Pre-" not in self.charger.get_charge_state() \
            else self.charger.get_precharge_threshold()
        duty = self.get_load_duty()
        status: ChargerStatus = self.charger.get_charger_status()
        temp = await self.temp_sensors.aread_temperature()
        time_data = time.time()
        test_data = TestData(
            temp_bat=temp[self.settings.temp_bat_addr],
            temp_env=temp[self.settings.temp_env_addr],
            temp_load=temp[self.settings.temp_load_addr],
            bat_current=bat_current,
            bat_voltage=bat_voltage,
            load_duty=duty,
            charge_status=status.charge_status,
            load_current=load_current,
            load_voltage=load_voltage,
            const_current=cc,
            const_voltage=cv,
            time=time_data)
        return test_data

    async def a_collect_data_loop(self) -> None:
        while True:
            await self.a_set_collected_parameters()
            gc.collect()

    async def a_show_parameters(self) -> None:
        while True:
            params = await self.a_get_collected_parameters()
            self._show_display(parameters=params)
            await asyncio.sleep(5)

    async def a_write_fs_loop(self):
        while True:
            await self.SENSOR_LOOP_STARTED.wait()

            while self.SENSOR_LOOP_STARTED.is_set():
                params = await self.a_get_collected_parameters()
                string = str(params) + "\n"
                with open(f"{self.SD_PATH}/{self.FILE_NAME}", "a") as f:
                    f.write(string)
                    f.flush()
                    print(string)
                gc.collect()

    async def a_set_collected_parameters(self) -> TestData:
        async with self.PARAMETERS_LOCK:
            self.__PARAMETERS = await self.acollect_parameters()

    async def a_get_collected_parameters(self) -> TestData:
        async with self.PARAMETERS_LOCK:
            params = self.__PARAMETERS
        return params
    
    async def a_hold_current_loop(self):
        while True:
            await self.CURRENT_HOLDER_STARTED.wait()
            self.set_load_duty(50)
            while self.CURRENT_HOLDER_STARTED.is_set():
                params = await self.a_get_collected_parameters()
                current = params.bat_current
                if current < self.HELD_CURRENT:
                    self.load.increase_current()
                else:
                    self.load.decrease_current()

    def collect_parameters(self) -> TestData:
        bat_voltage = self.multimeter.get_battery_mV()
        bat_current = self.multimeter.get_battery_mA()
        duty = self.get_load_duty()
        load_current = self.multimeter.get_load_mA()
        load_voltage = self.multimeter.get_load_mV()
        cc = self.charger.get_charge_current()
        cv = self.charger.get_charge_voltage()
        status: ChargerStatus = self.charger.get_charger_status()
        temp = self.temp_sensors.read_temperature()
        time_data = time.time()

        test_data = TestData(
            temp_bat=temp[self.settings.temp_bat_addr],
            temp_env=temp[self.settings.temp_env_addr],
            temp_load=temp[self.settings.temp_load_addr],
            bat_current=bat_current,
            bat_voltage=bat_voltage,
            load_duty=duty,
            charge_status=status.charge_status,
            load_current=load_current,
            load_voltage=load_voltage,
            const_current=cc,
            const_voltage=cv,
            time=time_data
        )
        return test_data

    async def acollect_parameters_json(self) -> str:
        test_data = await self.acollect_parameters()
        try:
            self.parameters_validation(test_data=test_data)
        except AssertionError as e:
            print(e)
            self.reset_all()
        return dumps(test_data)

    def collect_parameters_json(self) -> str:
        test_data = self.collect_parameters()
        try:
            self.parameters_validation(test_data=test_data)
        except AssertionError as e:
            print(e)
            self.reset_all()
        return dumps(test_data)

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

    def reset_charger(self) -> None:
        self.charger.reset()

    def reset_all(self) -> None:
        self.charger.reset()
        self.load.set_duty(0)

    def get_status(self) -> HeartBeatResponse:
        status = self.STATUS
        name = self.settings.device_name
        ip = self.get_device_ip()
        ch_status = self.charger.get_charger_status()

        resp = HeartBeatResponse(device_status=status, device_name=name, device_ip=ip, charger_status=ch_status)
        return resp
