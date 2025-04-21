
class DeviceAnnounce:
    def __init__(self, device_status: str, device_name: str, device_ip: str, sd_free_mem: int):
        self.device_status = device_status
        self.device_name = device_name
        self.device_ip = device_ip
        self.sd_free_mem = sd_free_mem


class StartSensors:
    def __init__(self, test_id, bat_id, sleep_time):
        self.test_id = test_id,
        self.bat_id = bat_id,
        self.sleep_time = sleep_time


class TestData:
    def __init__(
        self,
        temp_bat,
        temp_env,
        temp_load,
        bat_voltage,
        bat_current,
        load_voltage,
        load_current,
        load_duty,
        charge_status,
        const_current,
        const_voltage,
        time
    ):
        self.temp_bat = temp_bat
        self.temp_env = temp_env
        self.temp_load = temp_load
        self.load_voltage = load_voltage
        self.load_current = load_current
        self.bat_voltage = bat_voltage
        self.bat_current = bat_current
        self.load_duty = load_duty
        self.charge_status = charge_status
        self.const_current = const_current
        self.const_voltage = const_voltage
        self.time = time

    def __str__(self):
        # Формируем строку с параметрами в порядке их объявления
        return (
            f"temp_bat={self.temp_bat} "
            f"temp_env={self.temp_env} "
            f"temp_load={self.temp_load} "
            f"bat_voltage={self.bat_voltage} "
            f"bat_current={self.bat_current} "
            f"load_voltage={self.load_voltage} "
            f"load_current={self.load_current} "
            f"load_duty={self.load_duty} "
            f"charge_status={self.charge_status} "
            f"const_current={self.const_current} "
            f"const_voltage={self.const_voltage} "
            f"time={self.time}"
        )


class DischargeSettings:
    def __init__(self, dicharge_voltage_limit: int = 2750, current: int = 0,
                 start_duty: int = 0, temp_bat_limit: int = 50):
        self.discharge_current = current
        self.start_duty = start_duty
        self.dicharge_voltage_limit = dicharge_voltage_limit
        self.temp_bat_limit = temp_bat_limit


class StartCharge:
    def __init__(self, charge_settings):
        self.charge_settings = charge_settings


class WriteSettings:
    def __init__(self, sd_file_name: str = "test_data.txt", timeout: float = 1):
        self.sd_file_name = sd_file_name
        self.timeout = timeout


class StartSending:
    def __init__(self, db_url):
        self.db_url = db_url
