
import time
from device_manager.device_manager import DeviceSettings  # ,DeviceManager
import asyncio
from route_handlers.charge import start_charger_handler, stop_charge_handler
from route_handlers.load import set_load_duty_handler
from route_handlers.sensors import start_sensor_handler, stop_sensor_handler
from route_handlers.service import heartbeat_handler, reboot_handler, reset_handler
from utils import garbage_collect
from microdot import Microdot
import network
import ntptime


s = DeviceSettings(
    server_ip="192.168.0.37",
    server_port=61212,
    wifi_name="MDV",
    wifi_passw="QAZwsxedc",
    device_name="NodeMCUv3#1",
    device_port=21216,
    broadcast_port=45454,
    i2c_sda=21,
    i2c_scl=22,
    charger_intr=25,
    temp_pin=26,
    temp_bat_addr="289f4566542406eb",  # yellow, blue, green
    temp_load_addr="284c568f5424069e",  # whites
    temp_env_addr="28b89d9d5424065d",  # red, orange
    pwm_pin=27
)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(s.wifi_name, s.wifi_passw)
while not wlan.isconnected():
    print(f'Connecting to WIFI ({s.wifi_name})...')
    time.sleep(0.3)
ntptime.settime()

cfg = wlan.ipconfig('addr4')
# device_manager = DeviceManager(cfg, s)
print(cfg)

app = Microdot()


@garbage_collect
@app.route("/stop_charge")
async def stop_charge(request):
    res = await stop_charge_handler(device_manager, request)
    return res


@garbage_collect
@app.route("/start_charge")
async def start_charge(request):
    res = await start_charger_handler(device_manager, request)
    return res


@garbage_collect
@app.route("/set_load_duty")
async def set_load_duty(request):
    res = await set_load_duty_handler(device_manager, request)
    return res


@garbage_collect
@app.route("/stop_sensors")
async def stop_sensors(request):
    res = await stop_sensor_handler(device_manager, request)
    return res


@garbage_collect
@app.route("/start_sensors")
async def start_sensors(request):
    res = await start_sensor_handler(device_manager, request)
    return res


@garbage_collect
@app.route('/heartbeat')
async def heartbeat_route(request):
    res = await heartbeat_handler(device_manager, request)
    return res


@garbage_collect
@app.route("/reset")
async def reset_rout(request):
    res = await reset_handler(device_manager, request)
    return res


@garbage_collect
@app.route('/reboot')
async def reboot_route(request):
    res = await reboot_handler(device_manager, request)
    return res


async def main():
    asyncio.create_task(app.start_server("0.0.0.0", 21216))
    while True:
        await asyncio.sleep()
