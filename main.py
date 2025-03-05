from device_manager.device_manager import DeviceManager, DeviceSettings
import asyncio
from route_handlers.charge import start_charger_handler, stop_charge_handler
from route_handlers.load import set_load_duty_handler
from route_handlers.sensors import start_sensor_handler, stop_sensor_handler
from route_handlers.service import heartbeat_handler, reboot_handler, reset_handler
from utils import garbage_collect
from microdot import Microdot


s = DeviceSettings(
    device_name="NodeMCUv3#1",
    device_port=123,
    i2c_sda=4,
    i2c_scl=5,
    charger_intr=14,
    temp_pin=0,
    temp_bat_addr="289f4566542406eb",  # yellow, blue, green
    temp_load_addr="284c568f5424069e",  # whites
    temp_env_addr="28b89d9d5424065d",  # red, orange
    pwm_pin=12
)

device_manager = DeviceManager(s)


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
    corut = app.start_server("0.0.0.0", 5632)
    server = asyncio.create_task(corut)
    await server
