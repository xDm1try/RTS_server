from device_manager.drivers.bq25895 import ChargerStatus


class HeartBeatResponse:
    def __init__(self, device_status: str, device_name: str, device_ip: str, charger_status: ChargerStatus):
        self.device_status = device_status
        self.device_name = device_name
        self.device_ip = device_ip,
        self.charger_status = charger_status


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


class SetDuty:
    def __init__(self, new_duty):
        self.new_duty = new_duty


class StartCharge:
    def __init__(self, charge_settings):
        self.charge_settings = charge_settings
