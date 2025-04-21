import asyncio
import gc
import os
import aiohttp
from device_manager.drivers.display.display_device import DisplayDevice
from device_manager.drivers.l298n import L298N_short
from device_manager.drivers.bq25895 import BQ25895, ChargerSettings, ChargerStatus
from device_manager.drivers.ina3221 import INA3221
from device_manager.drivers.sdcard import SDCard
from device_manager.drivers.temperature_sensors import TemperatureSensors

# import os
# from device_manager.drivers.sdcard import SDCard
from server.models import TestData, DischargeSettings, WriteSettings
from ntptime import gmtime
from machine import Pin, SoftI2C, PWM, SPI
from onewire import OneWire
from json import dumps
import time


class DeviceSettings:

    def __init__(self,
                 server_ip: str,
                 server_port: int,
                 announce_route: str,
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
                 sdcard_CS: int,
                 ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.announce_route = announce_route
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


class CurrentActions:
    NOTHING = "NOTHING"
    CHARGING = "CHARGING"
    DISCHARGING = "DISCHARGING"


class DeviceManager:
    WRITE_LOOP_STARTED = asyncio.Event()
    VALIDATE_LOOP_STARTED = asyncio.Event()

    DISCHARGE_CURRENT_SETTINGS = DischargeSettings()

    CURRENT_ACTION = CurrentActions.NOTHING
    WRITE_SETTINGS = WriteSettings()

    EVENT_FIRST_TEST_DATA_APPEARED = asyncio.Event()

    PARAMETERS_LOCK = asyncio.Lock()

    def __init__(self, ip, settings: DeviceSettings):
        assert settings, "No settings in DeviceController"
        DeviceManager.EVENT_FIRST_TEST_DATA_APPEARED.clear()
        self.dev_ip = ip

        self.settings: DeviceSettings = settings
        self.display_spi = SPI(settings.display_spi, baudrate=60000000)
        self.display: DisplayDevice = DisplayDevice(
            self.display_spi, self.settings.display_DC, self.settings.display_RESET, self.settings.display_CS)
        self.init_all_devices()
        print("all_inited")
        time.sleep(1)

    def init_all_devices(self):
        try:
            self.SD_PATH = "/sd"
            print(gc.mem_free())
            sd = SDCard(SPI(self.settings.sdcard_SPI), Pin(self.settings.sdcard_CS))
            os.mount(sd, self.SD_PATH)
            assert "sd" in os.listdir("/"), "No sdcard mounted directory"

            self.i2c_bus = SoftI2C(scl=Pin(self.settings.i2c_scl), sda=Pin(self.settings.i2c_sda), freq=400000)
            self.onewire = OneWire(Pin(self.settings.temp_pin))
            self.pwm = PWM(Pin(self.settings.pwm_pin))

            self._init_charger()
            print("_init_charger")

            self._init_multimeter()
            print("_init_multimeter")

            self._init_temperature_sensors()
            print("_init_temperature_sensors")

            self._init_load()
            print("_init_load")
            self._init_display()
            print("_init_display")

        except Exception as e:
            e_str = str(e)
            self.display.write(e_str)
            raise e

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

    def _init_display(self):
        self._show_display()

    def get_free_sd_mem(self):
        data = os.statvfs(self.SD_PATH)
        gb = (data[0] * data[3]) // 1024 // 1024 // 1024
        return gb

    def _show_display(self, parameters: TestData | None = None):
        time_tuple: tuple = gmtime()
        time_str: str = f"{time_tuple[3]:02d}:{time_tuple[4]:02d}:{time_tuple[5]:02d}"
        params = parameters if parameters is not None else self.collect_parameters()
        charger_input = self.charger.get_input_type_str()
        writing_file = DeviceManager.WRITE_SETTINGS.sd_file_name \
            if DeviceManager.WRITE_LOOP_STARTED.is_set() else ""
        free_sd_gb = self.get_free_sd_mem()
        self.display.show(time_value=time_str, device_name=self.settings.device_name,
                          device_status=DeviceManager.CURRENT_ACTION, chg_status=params.charge_status,
                          v_bat=params.bat_voltage, current_bat=params.bat_current, temp_bat=params.temp_bat,
                          temp_env=params.temp_env, temp_load=params.temp_load, load_duty=params.load_duty,
                          ip=self.dev_ip, load_voltage=params.load_voltage,
                          load_current=params.load_current, input_status=charger_input,
                          const_current=params.const_current, const_volt=params.const_voltage,
                          writing_file=writing_file,
                          free_mem=free_sd_gb)

    async def acollect_parameters(self) -> TestData:
        # await asyncio.sleep(0)
        bat_voltage = self.multimeter.get_battery_mV()
        bat_current = self.multimeter.get_battery_mA()
        load_current = self.multimeter.get_load_mA()
        load_voltage = self.multimeter.get_load_mV()
        if "Disable" in self.charger.get_charge_state():
            cc = 0
            cv = 0
        else:
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
            DeviceManager.WRITE_SETTINGS = WriteSettings()
            await DeviceManager.WRITE_LOOP_STARTED.wait()

            print("file ", f"{self.SD_PATH}/{DeviceManager.WRITE_SETTINGS.sd_file_name}")
            while DeviceManager.WRITE_LOOP_STARTED.is_set():
                params = await self.a_get_collected_parameters()
                string = str(params) + "\n"
                with open(f"{self.SD_PATH}/{DeviceManager.WRITE_SETTINGS.sd_file_name}", "a") as f:
                    f.write(string)
                    f.flush()
                    print(string)
                gc.collect()
                await asyncio.sleep(DeviceManager.WRITE_SETTINGS.timeout)

    async def a_set_collected_parameters(self) -> None:
        # async with self.PARAMETERS_LOCK:
        self.__PARAMETERS = await self.acollect_parameters()
        self.a_hold_current(self.__PARAMETERS)
        if not self.EVENT_FIRST_TEST_DATA_APPEARED.is_set():
            self.EVENT_FIRST_TEST_DATA_APPEARED.set()

    async def a_get_collected_parameters(self) -> TestData:
        # async with self.PARAMETERS_LOCK:
        await self.EVENT_FIRST_TEST_DATA_APPEARED.wait()
        params = self.__PARAMETERS
        return params

    async def validate_data_loop(self) -> None:
        while True:
            errors = 0
            
            await DeviceManager.VALIDATE_LOOP_STARTED.wait()
            
            while DeviceManager.VALIDATE_LOOP_STARTED.is_set():
                await asyncio.sleep(1)
                data = await self.a_get_collected_parameters()
                if DeviceManager.CURRENT_ACTION == CurrentActions.CHARGING:
                    if data.temp_bat > self.charger.charge_settings.temp_bat_limit or \
                            data.bat_current < self.charger.charge_settings.cut_off_current_mA:
                        errors += 1
                        if errors > 5:
                            print("CHARGE STOPPED")
                            self.stop_charging()
                    else:
                        errors = 0
                if DeviceManager.CURRENT_ACTION == CurrentActions.DISCHARGING:
                    if data.temp_bat > DeviceManager.DISCHARGE_CURRENT_SETTINGS.temp_bat_limit or \
                            data.bat_voltage < DeviceManager.DISCHARGE_CURRENT_SETTINGS.dicharge_voltage_limit:
                        errors += 1
                        if errors > 5:
                            print("CHARGE STOPPED")
                            self.stop_discharging()
                    else:
                        errors = 0

    def a_hold_current(self, test_data: TestData) -> None:
        settings = DeviceManager.DISCHARGE_CURRENT_SETTINGS
        current = test_data.load_current
        if abs(settings.discharge_current - current) >= 5:
            if current < settings.discharge_current:
                self.load.increase_current(1)
            else:
                self.load.decrease_current(1)

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

    def get_load_duty(self) -> int:
        return self.load.get_duty()

    def set_load_duty(self, duty: int) -> None:
        return self.load.set_duty(duty)

    def start_charging(self, settings: ChargerSettings):
        self.charger.start_charging(settings)
        DeviceManager.CURRENT_ACTION = CurrentActions.CHARGING
        DeviceManager.VALIDATE_LOOP_STARTED.set()

    def stop_charging(self):
        self.charger.set_charge_enable(False)
        DeviceManager.CURRENT_ACTION = CurrentActions.NOTHING
        DeviceManager.VALIDATE_LOOP_STARTED.clear()

    def start_discharging(self, discharge_settings: DischargeSettings):
        DeviceManager.DISCHARGE_CURRENT_SETTINGS = discharge_settings
        print(discharge_settings)
        self.set_load_duty(discharge_settings.start_duty)
        DeviceManager.CURRENT_ACTION = CurrentActions.DISCHARGING
        DeviceManager.VALIDATE_LOOP_STARTED.set()

    def stop_discharging(self):
        DeviceManager.DISCHARGE_CURRENT_SETTINGS = DischargeSettings()
        self.set_load_duty(0)
        DeviceManager.CURRENT_ACTION = CurrentActions.NOTHING
        DeviceManager.VALIDATE_LOOP_STARTED.clear()

    def get_charging_settings(self) -> ChargerSettings:
        return BQ25895.charge_settings

    def reset_charger(self) -> None:
        self.charger.reset()

    def reset_all(self) -> None:
        self.stop_charging()
        self.start_discharging()
