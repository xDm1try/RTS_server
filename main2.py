import aiohttp
from device_manager.drivers.bq25895 import ChargerSettings
from microdot import Microdot
from device_manager.device_manager import DeviceManager, DeviceSettings
import json
from utils import garbage_collect, get_env_dict
import machine
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
gc.collect()
gc.collect()


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


async def send_heartbeat_response_loop(device_manager: DeviceManager):
    data = device_manager.settings
    while True:
        resp = await device_manager.get_status()
        resp = json.dumps(resp)
        async with aiohttp.ClientSession() as session:
            async with session.put(f'http://{data.server_ip}:{data.server_port}/device_announce',
                                   json=resp) as response:
                print("Status:", response.status)
        await asyncio.sleep(5)


@garbage_collect
@app.route("/health")
async def health(request):
    resp = json.dumps({"state": True, "heap_free": gc.mem_free()})
    return resp


@garbage_collect
@app.route("/stop_charge")
async def stop_charge(request):
    device_manager.stop_charging()


@garbage_collect
@app.route("/start_charge")
async def start_charge(request):
    data: ChargerSettings = request.json
    device_manager.start_charging(data)


@garbage_collect
@app.route("/set_load_duty")
async def set_load_duty(request):
    data = request.json
    new_duty = data.get("new_duty")
    device_manager.set_load_duty(new_duty)


@garbage_collect
@app.route("/stop_sensors")
async def stop_sensors(request):
    if not DeviceManager.SENSOR_LOOP:
        DeviceManager.SENSOR_LOOP.cancel()
        
@garbage_collect
@app.route("/get_sensors_data")
async def get_sensors(request):
    


# @garbage_collect
# @app.route("/start_sensors")
# async def start_sensors(request):
#     task = asyncio.create_task(device_manager.parameters_loop(device_manager=device_manager, request=request))
#     DeviceManager.SENSOR_LOOP = task


@garbage_collect
@app.route('/heartbeat')
async def heartbeat_route(request):
    resp = await device_manager.get_status()
    resp = json.dumps(resp)
    return resp


@garbage_collect
@app.route("/reset")
async def reset_rout(request):
    device_manager.reset_all()


@garbage_collect
@app.route('/reboot')
async def reboot_route(request):
    machine.reset()
    gc.collect()


async def main():
    await asyncio.create_task(app.start_server("0.0.0.0", 21216))
    while True:
        gc.collect()
        print(gc.mem_free())
        await asyncio.sleep(2)
