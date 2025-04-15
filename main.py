import gc
from  network import WLAN ,STA_IF
# from  ntptime import gmtime, settime
from time import sleep
# import aiohttp
gc.collect()


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

import asyncio

import json
from device_manager.device_manager import DeviceManager, DeviceSettings
from device_manager.drivers.bq25895 import ChargerSettings
from server.microdot import Microdot

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

# async def send_heartbeat_response_loop(d: DeviceManager):
#     data = d.settings
#     while True:
#         resp = await d.get_status()
#         resp = json.dumps(resp)
#         async with aiohttp.ClientSession() as session:
#             async with session.put(f'http://{data.server_ip}:{data.server_port}/device_announce',
#                                    json=resp) as response:
#                 print("Status:", response.status)
#         await asyncio.sleep(5)


@garbage_collect
@app.route("/health")
async def health(request):
    resp = json.dumps({"state": True, "heap_free": gc.mem_free()})
    return resp


@garbage_collect
@app.route("/stop_charge")
async def stop_charge(request):
    d.stop_charging()


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


@garbage_collect
@app.route("/set_load_duty")
async def set_load_duty(request):
    data = request.json
    new_duty = int(data.get("new_duty"))
    d.set_load_duty(new_duty)


@garbage_collect
@app.route("/stop_sensors")
async def stop_sensors(request):
    if DeviceManager.SENSOR_LOOP is not None:
        DeviceManager.SENSOR_LOOP_TEMINATED.set()

@garbage_collect
@app.route("/start_sensors")
async def start_sensors(request):
    if DeviceManager.SENSOR_LOOP is None:
        DeviceManager.SENSOR_LOOP_TEMINATED.clear()
        DeviceManager.SENSOR_LOOP = asyncio.create_task(d.a_write_fs_loop())


@garbage_collect
@app.route("/get_sensors_data")
async def get_sensors(request):
    ...


@garbage_collect
@app.route('/heartbeat')
async def heartbeat_route(request):
    resp = await d.get_status()
    resp = json.dumps(resp)
    return resp


@garbage_collect
@app.route("/reset")
async def reset_rout(request):
    d.reset_all()

# import asyncio;asyncio.run(main())
async def main():
    asyncio.create_task(app.start_server("0.0.0.0", 21216))
    asyncio.create_task(d.a_collect_data_loop())
    asyncio.create_task(d.a_show_parameters())
    while True:
        gc.collect()
        print(gc.mem_free())
        await asyncio.sleep(2)
