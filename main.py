import json
from network import WLAN, STA_IF
import gc
from time import sleep
print("STARTED")
print(gc.mem_free())
wlan = WLAN(STA_IF)
wlan.active(True)
wlan.connect("MDV", "QAZwsxedc")
while not wlan.isconnected():
    print('Connecting to WIFI')
    sleep(0.3)
print("CONNECTED")
gc.collect()
# while gmtime()[0] == 2000:
#     settime()
#     sleep(0.3)
gc.collect()
cfg = wlan.ipconfig('addr4')
print(cfg)
sleep(0.3)
print("DONE")
# import aiohttp
gc.collect()

import asyncio
from device_manager.device_manager import DeviceManager, DeviceSettings
from device_manager.drivers.bq25895 import ChargerSettings
from server.microdot import Microdot
from server.models import DischargeSettings, WriteSettings


def garbage_collect(func):
    def decorator():
        func()
        gc.collect()
    return decorator


def get_env_dict(device_settings_file: str = "/core/device_settings.env") -> dict:
    new_dict = dict()
    with open(device_settings_file, "r") as f:
        lines = f.readlines()
        lines = list(map(lambda line: line.strip(), lines))
        items: list[(str, str)] = list(map(lambda line: line.split("="), lines))
        for name, value in items:
            new_dict[name.strip()] = value.strip()

    return new_dict


d = get_env_dict()

s = DeviceSettings(
    server_ip=d.get("SERVER_IP"),
    server_port=int(d.get("SERVER_PORT")),
    announce_route=d.get("ANNOUNCE_ROUTE"),
    wifi_name=d.get("WIFI_NAME"),
    wifi_passw=d.get("WIFI_PASSW"),
    device_name=d.get("DEVICE_NAME"),
    device_port=int(d.get("DEVICE_PORT")),
    broadcast_port=int(d.get("BROADCAST_PORT")),
    i2c_sda=int(d.get("I2C_SDA")),
    i2c_scl=int(d.get("I2C_SCL")),
    charger_intr=int(d.get("CHARGER_INTR")),
    temp_pin=int(d.get("TEMP_PIN")),
    temp_bat_addr=d.get("TEMP_BAT_ADDR"),  # yellow, blue, green
    temp_load_addr=d.get("TEMP_LOAD_ADDR"),  # whites
    temp_env_addr=d.get("TEMP_ENV_ADDR"),  # red, orange
    pwm_pin=int(d.get("PWM_PIN")),
    display_spi=int(d.get("DISPLAY_SPI")),
    display_DC=int(d.get("DISPLAY_DC")),
    display_RESET=int(d.get("DISPLAY_RESET")),
    display_CS=int(d.get("DISPLAY_CS")),
    sdcard_SPI=int(d.get("SDCARD_SPI")),
    sdcard_CS=int(d.get("SDCARD_CS"))
)

cfg = wlan.ipconfig('addr4')
gc.collect()
print(gc.mem_free())
print(cfg)

d = DeviceManager(cfg[0], s)

app = Microdot()


@garbage_collect
@app.route("/health")
async def health(request):
    resp = json.dumps({"state": True, "heap_free": gc.mem_free()})
    return resp


@garbage_collect
@app.route("/stop_charge")
async def stop_charge(request):
    d.stop_charging()
    return {}


@garbage_collect
@app.route("/start_charge")
async def start_charge(request):
    data: ChargerSettings = request.json
    print(f"{data=}")
    cs = ChargerSettings(const_current_mA=data["const_current_mA"],
                         const_volt_mV=data["const_volt_mV"],
                         cut_off_current_mA=data["cut_off_current_mA"],
                         temp_bat_limit=data["temp_bat_limit"])

    d.start_charging(cs)
    return {}


@garbage_collect
@app.route("/start_discharge")
async def set_load_duty(request):
    d.stop_charging()
    data = request.json
    discharge_current = int(data.get("discharge_current"))
    start_duty = int(data.get("start_duty", 50))
    limit_voltage = int(data.get("dicharge_voltage_limit", 2750))
    bat_temp_limit = int(data.get("temp_bat_limit", 50))
    settings = DischargeSettings(dicharge_voltage_limit=limit_voltage,
                                 current=discharge_current,
                                 start_duty=start_duty,
                                 temp_bat_limit=bat_temp_limit)
    d.start_discharging(settings)
    return {}


@garbage_collect
@app.route("/stop_discharge")
async def stop_discharge(request):
    d.stop_discharging()
    return {}


@garbage_collect
@app.route("/start_writing")
async def start_sensors(request):
    data = request.json
    file_name = str(data.get("sd_file_name", "test_data_params.txt"))
    timeout = float(data.get("timeout", 1))
    
    with open(f'{d.SD_PATH}/{file_name}', "w") as f:
        f.write("")
        f.flush()
                
    DeviceManager.WRITE_SETTINGS = WriteSettings(sd_file_name=file_name, timeout=timeout)
    DeviceManager.WRITE_LOOP_STARTED.set()
    return {}


@garbage_collect
@app.route("/stop_writing")
async def stop_sensors(request):
    DeviceManager.WRITE_LOOP_STARTED.clear()
    return {}


@garbage_collect
@app.route("/get_sensors_data")
async def get_sensors(request):
    test_data = await d.a_get_collected_parameters()
    return test_data.__dict__


@garbage_collect
@app.route("/reset")
async def reset_rout(request):
    import machine
    machine.reset()



def set_exception_handler() -> None:
    def handle_exception(loop, context):
        print(context["exception"])
        d.stop_charging()
        d.stop_discharging()
        d.display.write(context["exception"])
        loop.stop()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


async def main():
    set_exception_handler()
    asyncio.create_task(app.start_server("0.0.0.0", 21216))
    asyncio.create_task(d.a_collect_data_loop())
    asyncio.create_task(d.a_show_parameters())
    asyncio.create_task(d.a_write_fs_loop())
    # asyncio.create_task(d.validate_data_loop())
    asyncio.create_task(d.a_send_device_announce_loop())
    while True:
        gc.collect()
        print(gc.mem_free())
        await asyncio.sleep(2)

asyncio.run(main())