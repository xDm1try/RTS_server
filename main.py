import gc
import network
import asyncio
import time
gc.collect()
time.sleep(3)
gc.collect()
print(gc.mem_free())
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("POCOF3", "22222222")
while not wlan.isconnected():
    print('Connecting to WIFI')
    time.sleep(0.3)
time.sleep(0.3)

gc.collect()
from utils import garbage_collect, get_env_dict
from route_handlers import heartbeat_handler, reboot_handler, reset_handler
gc.collect()
from route_handlers import start_sensor_handler, stop_sensor_handler
from route_handlers import set_load_duty_handler
from route_handlers import start_charger_handler, stop_charge_handler
gc.collect()
import json
from device_manager.device_manager import DeviceManager, DeviceSettings
gc.collect()
from microdot import Microdot


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
    pwm_pin=int(d.get("PWM_PIN"))
)

cfg = wlan.ipconfig('addr4')

print(gc.mem_free())
print(cfg)

device_manager = DeviceManager(cfg[0], s)

app = Microdot()

@garbage_collect
@app.route("/health")
async def health(request):
    resp = json.dumps({"state": True, "heap_free": gc.mem_free()})
    return resp


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

gc.collect()


async def main():
    await asyncio.create_task(app.start_server("0.0.0.0", 21216))
    while True:
        gc.collect()
        print(gc.mem_free())
        await asyncio.sleep(2)
